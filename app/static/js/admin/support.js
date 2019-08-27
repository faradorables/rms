let _page, _limit, _total_data;

function _supports(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    _supports_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

function supportForm(){
  $('#supportForm').modal('show');
  _subject_support_list();
  var date = new Date();
  var components = ['ION-',
      date.getDate(),
      date.getHours(),
      date.getMinutes(),
      date.getSeconds(),
      date.getMilliseconds()
  ];

  var id = components.join("");
  console.log(id)
}

$('#supportForm').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function randomTicket(){
  var date = new Date();
  var components = [
      date.getYear(),
      date.getMonth(),
      date.getDate(),
      date.getHours(),
      date.getMinutes(),
      date.getSeconds(),
      date.getMilliseconds()
  ];

  var id = components.join("");
  console.log(id)
}

function _subject_support_list(){
  _loading(1);
  $.post('/api/v1/ams/subject_support',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _subject_support_append(e.data[i], i);
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

function _subject_support_append(data){
  $('#subject_body').append(
    '<option value="'+ data.id +'">'+ data.name +'</option>'
  )
}

function _supports_list(page){
  _loading(1);
  $.post('/api/v1/ams/support',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_support.total_support;
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
      $('#total_supports, .total_data').text(_total_data);
      $('#total_solved').text(e.count_support.total_solved);
      $('#total_onprocess').text(e.count_support.total_onprocess);
      $('#total_unsolved').text(e.count_support.total_unsolved);
      $('#total_cancelled').text(e.count_support.total_cancelled);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _supports_append(e.data[i]);
        }
      }else{
        $('#data_body').append(
          '<div class="_notif_menu"><i class="fa fa-exclamation-triangle"></i>User dari sektor ini belum tersedia.</div>'
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
    _supports_list(_page)
  }
}

// PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _supports_list(_page)
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

// APPENDING THE supports
function _supports_append(data){
  console.log(data)
  $('#data_body').append(
    '<div onclick="supportDetail('+data.id+')">' +
    '<div class="id">' + data.id + '</div>' +
    '<div class="ticket_number">' + data.ticket_number + '</div>' +
    '<div class="id_user">' + data.id_user + '</div>' +
    // '<div class="id_subject">' + data.id_subject + '</div>' +
    '<div class="name_subject">' + data.name_subject + '</div>' +
    '<div class="title">' + data.title + '</div>' +
    // '<div class="description">' + data.description + '</div>' +
    '<div class="status">' + data.name_status + '</div>' +
    '<div class="option">' +
    '<a><i class="fas fa-info-circle"></i></a>' +
    '<a><i class="fas fa-ban"></i></a>' +
    '</div>' +
    '</div>'
  )
}

function supportDetail(id){
  _loading(1);
  $.post('/api/v1/ams/support_detail',{
      'id_admin': userData['id'],
      'token': userData['token'],
      'status': 0,
      'id': id,
  }, function (e) {
    let i;
      if(e['status'] === '00'){
        if (id > 0){
          $('#detail_id').text(e.id.id);
          $('#ticket_number').text(e.id.name_status);
          $('#title_support').text(e.id.title);
          $('#description_support').text(e.id.description);
          // console.log(e.id.role_name);
          // $('#detail_id').click(function(){
          //   console.log(e.id.id);
          //   // editForm(id);
          // });
console.log(e.id.title)
        }else{
          notif('danger', 'System Error!', 'user tidak terdaftar')
        }
    }else{
      notif('danger', 'System Error!', e.message);
    }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });

  $('#supportDetail').modal('show');
  console.log(id);
}

$('#supportDetail').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})
