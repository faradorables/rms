let _page, _limit, _total_data;

function _sent(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    _sent_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

function _trash(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    _trash_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

function composeForm(){
  $('#composeForm').modal('show');
  _message_category()
}

$('#composeForm').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function add_message(){
  var subject = document.getElementById("subject").value;
  var product_cat = document.getElementById("category_body").value;
  var link = document.getElementById("link").value;
  var content = document.getElementById("content").value;
  var text = new Blob([''], { type: "text/plain"})
  var formData = new FormData();
  formData.append('id', text, userData['id']);
  formData.append('token', text, userData['token']);
  formData.append('subject', text, subject);
  formData.append('product_cat', text, product_cat);
  formData.append('link', text, link);
  formData.append('content', text, content);
  // Attach file
  formData.append('image', $('input[type=file]')[0].files[0]);

  _loading(1);
  $.ajax({
    url: '/api/v1/ams/add_message',
    data: formData,
    type: 'POST',
    contentType: false, // NEEDED, DON'T OMIT THIS (requires jQuery 1.6+)
    processData: false, // NEEDED, DON'T OMIT THIS
    success: function(e){
      notif('success', 'Success!', e['messages']);
    },
    error:function(e){
        notif('danger', 'System Error!', e['messages']);
    },
    // ... Other options like success and etc
});

  // _loading(1);
  // $.post('/api/v1/ams/add_message',{
  //     'data': userData['id'],
  //     'token': userData['token']
  //     // 'subject': subject,
  //     // 'product_cat': product_cat,
  //     // 'content': content,
  //     // 'link': link,
  //     // 'image': image
  // }, function (e) {
  //   if(e['status'] === '00'){
  //     console.log(e['messages'])
  //     notif('success', 'Success!', e['messages']);
  //
  //   }else{
  //     notif('danger', 'System Error!', e['messages']);
  //   }
  // }).fail(function(){
  //   notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  // }).done(function(){
  //   _loading(0);
  // });
  _sent_list(_page);
}

function _sent_list(page){
  _loading(1);
  $.post('/api/v1/ams/sent_message',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_message.total_message;
      $('.small_data').text((_page*_limit)+1)
      let _big_data = (_page+1)*_limit;
      console.log('test');

      let _max = parseInt(_total_data/_limit);
      if(_big_data >= _total_data){
        console.log('test');
        _big_data = _total_data;
      }
      _check_arrow(_max);
      $('.big_data').text(_big_data);
      $('#total_message, .total_data').text(_total_data);
      $('#total_trash').text(e.count_message.total_trash);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _sent_append(e.data[i]);
          console.log(e.data);
        }
      }else{
        $('#data_body').append(
          '<div class="_notif_menu"><i class="fa fa-exclamation-triangle"></i>admin dari sektor ini belum tersedia.</div>'
        )
      }
    }else{
      notif('danger', 'System Error!', e.message);
    }
    console.log(e.data.length)
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function _trash_list(page){
  _loading(1);
  $.post('/api/v1/ams/trash_message',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_message.trash_message;
      $('.small_data').text((_page*_limit)+1)
      let _big_data = (_page+1)*_limit;
      console.log('test');

      let _max = parseInt(_total_data/_limit);
      if(_big_data >= _total_data){
        console.log('test');
        _big_data = _total_data;
      }
      _check_arrow(_max);
      $('.big_data').text(_big_data);
      $('#total_message, .total_data').text(_total_data);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _sent_append(e.data[i]);
          console.log(e.data);
        }
      }else{
        $('#data_body').append(
          '<div class="_notif_menu"><i class="fa fa-exclamation-triangle"></i>admin dari sektor ini belum tersedia.</div>'
        )
      }
    }else{
      notif('danger', 'System Error!', e.message);
    }
    console.log(e.data.length)
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}
// NEXT PAGE BUTTON
function _next_page(){
  if((_page + 1)*25<_total_data){
    _page += 1;
    _sent_list(_page)
  }
}

// PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _sent_list(_page)
  }
}

// CHECKING THE PAGE AND THE ARROW
function _check_arrow(max){
  $('.left_arrow, .right_arrow').removeClass('disabled');
  if(_page === 0 && _page != max){
    $('.left_arrow').addClass('disabled');
  }else if(_page === 0 && _page === max){
    $('.left_arrow, .right_arrow').addClass('disabled');
  }else if(_page === max){
    $('.right_arrow').addClass('disabled');
  }
}

function _sent_append(data){
  console.log('data')
  $('#data_body').append(
    '<table class="table">'+
    '<tbody>'+
    '<tr class="unread">'+
    '<td>'+
    '<div onclick="messageDetail('+data.id+')">' +
    '<div class="subject">' + data.subject + '</div>' +
    '</td>'+
    '<td>'+
    // '<div class="subject">' + data.subject + '</div>' +
    '<div class="summary">' + data.content + '</div>' +
    '</td>'+
    '<td>'+
    '<span class="time">' + data.date+'-'+data.month+'-'+data.year+' '+ data.time + '</span>' + '<br>'+
    '</td>'+
    '<td>'+
    '<span class="option">' +
    '<a><i class="fa fa-exclamation-triangle"></i></a>' +
    '<a><i class="fa fa-star"></i></a>' +
    '<a onclick="delete_message('+data.id+')"><i class="fa fa-trash"></i></a>' +
    '</span>' +
    '</div>'+
    '</td>'+
    '</tr>'+
    '</tbody>'+
    '</table>'
  )
  $('#content').text(data.content);
}

function delete_message(id){
  _loading(1);
  $.post('/api/v1/delete_message',{
    'id_admin': userData['id'],
    'id':id,

  }, function (e) {
    if(e['status'] === '00'){
      console.log(e['messages'])
      notif('success', 'Success!', e['messages']);

    }else{
      notif('danger', 'System Error!', e['messages']);
    }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
    _sent_list(_page);
  });
}

function _message_category(){
  _loading(1);
  $.post('/api/v1/ams/message_category',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _message_category_append(e.data[i], i);
          console.log(i);
        }
      }
    }else{
      notif('danger', 'System Error!', e.message);
    }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function _message_category_append(data){
  $('#category_body').append(
    '<option value="'+ data.id +'">'+ data.name +'</option>'
  )
}
