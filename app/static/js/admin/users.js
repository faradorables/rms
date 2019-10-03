let _page, _limit, _total_data;

function numberWithCommas(number) {
    var parts = number.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}
$(document).ready(function() {
  $("#total_wallet").each(function() {
    var num = $(this).text();
    var commaNum = numberWithCommas(num);
    $(this).text(commaNum);
  });
});

function _users(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    _user_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

// ========================================================
// users LIST
// ========================================================

// CALL THE users
function _user_list(page){
  _loading(1);
  $.post('/api/v1/ams/users',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_user.total_user;
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
      $('#total_users, .total_data').text(_total_data);
      $('#total_outlet').text(e.count_user.total_outlet);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _user_append(e.data[i], i+1);
          // console.log(e.data);
        }
      }else{
        $('#data_body').append(
          '<div class="_notif_menu"><i class="fa fa-exclamation-triangle"></i>User dari sektor ini belum tersedia.</div>'
        )
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

// NEXT PAGE BUTTON
function _next_page(){
  if((_page + 1)*25<_total_data){
    _page += 1;
    _user_list(_page)
  }
}

// PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _user_list(_page)
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

function _user_append(data, i){
  $('#data_body').append(
    '<tr onclick="modalDetail('+data.id+')">'+
    '<td>' + i + '</td>' +
    '<td>' + data.name + '</td>' +
    '<td>'+data.email + '</td>' +
    '<td>'+data.phone_number + '</td>' +
    '<td>'+
    '<a><i class="fas fa-info-circle"></i></a>' +
    '<a><i class="fas fa-ban"></i></a>' +
    '</td>'+
    '</tr>'+
    '</table>'
  )
}

function modalDetail(id){
  _loading(1);
  $.post('/api/v1/ams/userdetail',{
      'id_admin': userData['id'],
      'token': userData['token'],
      'status': 0,
      'user_id': id,
  }, function (e) {
    let i;
      if(e['status'] === '00'){
        if (id > 0){
          _users_outlet(id);
          $('#detail_name').text(e.id.name);
          $('#detail_phone').text(e.id.phone_number);
          $('#detail_email').text(e.id.email);
          $('#detail_address').text(e.id.address);
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
  $('#modalDetail').modal('show');
}

$('#modalDetail').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function _users_outlet(id){
  $.post('/api/v1/ams/outlet',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'user_id': id,
      'page': 0
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      $('#data_outlet').empty();
      $('#outlet_by_user').text(e.count_user.outlet_by_user);
      if(e.useroutlet.length > 0){
        for(i=0; i < e.useroutlet.length; i++){
          _outlet_append(e.useroutlet[i], i+1);
        }
      }else{
        $('#data_outlet').append(
          '<div class="_notif_menu"><i class="fa fa-exclamation-triangle"></i>User ini belum memiliki outlet</div>'
        )
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

function _outlet_append(useroutlet, i){
  $('#data_outlet').append(
    '<tr>'+
    '<td onclick="modalDetail('+useroutlet.id+')">' + i + '</td>' +
    '<td>' + useroutlet.name + '</td>' +
    '<td>' + useroutlet.phone_number + '</td>' +
    '<td>' + useroutlet.address + '</td>' +
    '<td>' + useroutlet.city + '</td>' +
    '<td>' + useroutlet.province + '</td>' +
    '<td>'+
    '<a onclick="editPrice('+useroutlet.id+')"><i class="fas fa-info-circle"></i></a>' +
    '<a><i class="fas fa-ban"></i></a>' +
    '</td>'+
    '</tr>'+
    '</table>'
  )
}
