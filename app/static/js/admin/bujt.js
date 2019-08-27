let _page, _limit, _total_data;
// var _obu_uid;

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
    _users_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

// ========================================================
// users LIST
// ========================================================

// CALL THE users
function _users_list(page){
  _loading(1);
  $.post('/api/v1/ams/bujt',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_user.total_bujt;
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
      $('#total_active_users').text(e.count_user.active_bujt);
      $('#total_wallet').text('Rp ' + e.total_wallet);
      $('#total_trx').text(e.total_trx.total_trx);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _users_append(e.data[i], i+1);
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

// function _users_upgraded(page){
//   _loading(1);
//   $.post('/api/v1/ams/users_upgraded',{
//       'id': userData['id'],
//       'token': userData['token'],
//       'status': 0,
//       'page': page,
//       'sector_id': $('#sector_id').val(),
//   }, function (e) {
//     let i;
//     if(e['status'] === '00'){
//       _total_data = e.count_user.total_user;
//       $('.small_data').text((_page*_limit)+1)
//       let _big_data = (_page+1)*_limit;
//       console.log('test');
//       let _max = parseInt(_total_data/_limit);
//       if(_big_data >= _total_data){
//         console.log('test');
//         _big_data = _total_data;
//       }
//       _check_arrow(_max);
//       $('.big_data').text(_big_data);
//       $('#total_users, .total_data').text(_total_data);
//       $('#total_active_users').text(e.count_user.active_bujt);
//       $('#total_wallet').text('Rp ' + e.total_wallet);
//       $('#total_trx').text('Rp ' + e.total_trx);
//       $('#data_body').empty();
//       if(e.data.length > 0){
//         for(i=0; i < e.data.length; i++){
//           _users_append(e.data[i], i+1);
//           // console.log(e.data);
//         }
//       }else{
//         $('#data_body').append(
//           '<div class="_notif_menu"><i class="fa fa-exclamation-triangle"></i>User dari sektor ini belum tersedia.</div>'
//         )
//       }
//     }else{
//       notif('danger', 'System Error!', e.message);
//     }
//   }).fail(function(){
//     notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
//   }).done(function(){
//     _loading(0);
//   });
// }

function _users_suspended(page){
  _loading(1);
  $.post('/api/v1/ams/users_suspended',{
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
      $('#total_active_users').text(e.count_user.active_bujt);
      $('#total_wallet').text('Rp ' + e.total_wallet);
      $('#total_trx').text('Rp ' + e.total_trx);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _users_append(e.data[i], i+1);
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
    _users_list(_page)
  }
}

// PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _users_list(_page)
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

// APPENDING THE users
function _users_append(data, i){
  // upgradeDetail(data.id_upgrade);
  $('#data_body').append(
    '<div onclick="modalDetail('+data.id+')">' +
    '<div class="no">' + i + '</div>' +
    '<div><div class="profilePicture"></div></div>' +
    '<div class="name">' + data.name + '</div>' +
    '<div class="email">' + data.email + '</div>' +
    '<div class="phone">' + data.phone_number + '</div>' +
    '<div class="value">Rp ' + data.wallet + '</div>' +
    '<div class="option">' +
    '<a><i class="fas fa-info-circle"></i></a>' +
    '<a><i class="fas fa-ban"></i></a>' +
    '</div>' +
    '</div>'
  )
}


function _trx_all_append(client, i){
  $('#data_trx_all').append(
    '<tr onclick="translog_detail_modal(\'' + client.id + '\', \'' + client.obu_uid + '\')">'+
    '<td>' + i + '</td>' +
    '<td>' + client.obu_uid + '</td>' +
    '<td>' + client.plaza_in_name + '</td>' +
    '<td>' + client.plaza_out_name + '</td>' +
    '<td>' + client.price + '</td>' +
    '<td>' + client.time_in + '</td>' +
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
          _client_transaction(e.id.client_id);
          $('#detail_name').text(e.id.name);
          $('#detail_phone').text(e.id.phone);
          $('#detail_email').text(e.id.email);
          $('#user_total_wallet').text('Rp ' + e.id.wallet);
          $('#user_total_obu').text(+ e.id.total_obu);
          $('#user_total_trx').text(e.id.client_trx);
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

function trx_all_modal(){
  $('#trxallmodal').modal('show');
}

$('#trxallmodal').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function translog_detail_modal(_id, _obu_uid){
_loading(1);
$.post('/api/v1/ams/client_history',{
    'id': userData['id'],
    'token': userData['token'],
    'status': 1,
    '_obu_uid': _obu_uid,
    '_id': _id
}, function (e) {
  let i;
    if(e['status'] === '00'){
      $('#obu_uid').text(e.data.obu_uid);
      $('#plate_id').text(e.data.plate_id);
      $('#user_name').text(e.data.user_name);
      $('#user_id').text(e.data.user_id);
      $('#vehicle_class_name').text(e.data.vehicle_class_name);
      $('#plaza_in_name').text(e.data.plaza_in_name);
      $('#plaza_out_name').text(e.data.plaza_out_name);
      $('#lane_in_name').text(e.data.lane_in_name);
      $('#lane_out_name').text(e.data.lane_out_name);
      $('#time_in').text(e.data.time_in);
      $('#time_out').text(e.data.time_out);
      $('#refca_in').text(e.data.refca_in);
      $('#refca_out').text(e.data.refca_out);
      $('#price').text(e.data.price);
  }else{
    notif('danger', 'System Error!', e.message);
  }
}).fail(function(){
  notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
}).done(function(){
  _loading(0);
});

  $('#translogdetailmodal').modal('show');
}

$('#translogdetailmodal').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function bujtPassword(){
  _loading(0);
  $('#bujtPassword').modal('show');
}

$('#bujtPassword').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function redirect_to_form() {
  var password = document.getElementById("password").value;
  _loading(1);
  $.post('/api/v1/auth/verif_password',{
    'id': userData['id'],
    'token': userData['token'],
    'password': password
  }, function(e){
    console.log(userData['id']);
      if(e['status'] === '00'){
          bujtForm();
      }else{
          nav_href('BUJT');
          notif('danger', 'Authentication failed', e.message)
      }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function bujtForm(){
  $('#bujtForm').modal('show');
  _trxtype_list();
}

$('#bujtForm').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function add_client(){
  var name = document.getElementById("name").value;
  var phone = document.getElementById("phone").value;
  var email = document.getElementById("email").value;
  var trxtype = document.getElementById("trxtype").value;
  var pin = document.getElementById("pin").value;

  _loading(1);
  $.post('/api/v1/add_client',{
      'id': userData['id'],
      'token': userData['token'],
      'name': name,
      'phone': phone,
      'email': email,
      'trxtype': trxtype,
      'pin': pin
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
    nav_href('BUJT');
    _loading(0);
  });
}

function _trxtype_list(){
  _loading(1);
  $.post('/api/v1/ams/trxtype',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _trxtype_append(e.data[i], i);
          console.log(i);
        }
      }

      console.log(document.getElementById("role_body2"));
    }else{
      notif('danger', 'System Error!', e.message);
    }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function _trxtype_append(data){
  $('#trxtype').append(
    '<option value="'+ data.id +'">'+ data.name +'</option>'
  )
}

function _client_transaction(client_id){
  $.post('/api/v1/ams/client_history',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'client_id': client_id,
      'skip':0
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      $('#data_trx').empty();
      if(e.client.length > 0){
        for(i=0; i < e.client.length; i++){
          _trx_append(e.client[i], i+1);
        }
        for(i=0; i < e.client.length; i++){
          _trx_all_append(e.client[i], i+1);
        }
      }else{
        $('#data_trx').append(
          '<div class="_notif_menu"><i class="fa fa-exclamation-triangle"></i>User ini belum memiliki riwayat transaksi</div>'
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

function _trx_append(client, i){
  $('#data_trx').append(
    '<tr onclick="translog_detail_modal(\'' + client.id + '\', \'' + client.obu_uid + '\')">'+
    '<td>' + i + '</td>' +
    '<td>' + client.obu_uid + '</td>' +
    '<td>' + client.plaza_in_name + '</td>' +
    '<td>' + client.plaza_out_name + '</td>' +
    '<td>' + client.price + '</td>' +
    '<td>' + client.time_in + '</td>' +
    '</tr>'+
    '</table>'
  )
}
// function direct_page_bujt(){
//   $('#bujtPassword').modal('hide');
//   nav_href('BUJT');
//   _loading(0);
// }
//
// $('#bujtPassword').on('hide.bs.modal', function () {
//   $(this).css({'padding': '0'})
// })
