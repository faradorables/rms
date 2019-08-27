let _page, _limit, _total_data;
var userid;


function list_request_upgrade(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    _users_request();
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

function _users_request(page){
  // console.log(page)
  _loading(1);
  $.post('/api/v1/ams/users_request_upgrade',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': 0,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_user.users_request_upgrade;
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
      $('#total_active_users').text(e.count_user.active_user);
      $('#total_wallet').text('Rp ' + e.total_wallet);
      $('#total_trx').text('Rp ' + e.total_trx);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _users_request_append(e.data[i], i+1);
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

function _next_page(){
  if((_page + 1)*25<_total_data){
    _page += 1;
    _users_request(_page)
  }
}

// PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _users_request(_page)
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

function upgradeDetail(id){
  _loading(1);
  $.post('/api/v1/ams/upgradedetail',{
      'id_admin': userData['id'],
      'token': userData['token'],
      'status': 0,
      'id_upgrade': id,
  }, function (e) {
    let i;
      if(e['status'] === '00'){
        userid = e.data.user_id;
        document.getElementById("selfie_photo").src= e.data.selfie_photo;
        document.getElementById("id_card").src= e.data.id_card;
        $('#id_upgrade').text(e.data.id);
        $('#user_id').text(e.data.user_id);
        $('#status_upgrade').text(e.data.status_upgrade);
      }else{
        notif('danger', 'System Error!', e.message);
      }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
  $('#upgradeDetail').modal('show');
}

$('#upgradeDetail').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function upgrade_approval(){
  _loading(1);
  $.post('/api/v1/upgrade_approval',{
    'id_admin': userData['id'],
    'token': userData['token'],
    '_status_upgrade': 2,
    '_user_id': userid

  }, function (e) {
    if(e['status'] === '00'){
      list_request_upgrade();
      console.log(e['messages'])
      notif('success', 'Success!', e['messages']);

    }else{
      notif('danger', 'System Error!', e['messages']);
    }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function upgrade_rejection(){
  _loading(1);
  $.post('/api/v1/upgrade_approval',{
    'id_admin': userData['id'],
    'token': userData['token'],
    '_status_upgrade': 3,
    '_user_id': userid
  }, function (e) {
    if(e['status'] === '00'){
      list_request_upgrade();
      console.log(e['messages'])
      notif('success', 'Success!', e['messages']);
    }else{
      notif('danger', 'System Error!', e['messages']);
    }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function verif_password_acc() {
  var password = document.getElementById("password").value;
  _loading(1);
  $.post('/api/v1/auth/verif_password',{
    'id': userData['id'],
    'token': userData['token'],
    'password': password,
  }, function(e){
    console.log(userData['id']);
      if(e['status'] === '00'){
          upgrade_approval();
      }else{
          notif('danger', 'Authentication failed', e.message)
      }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function verif_password_reject() {
  var password1 = document.getElementById("password1").value;
  _loading(1);
  $.post('/api/v1/auth/verif_password',{
    'id': userData['id'],
    'token': userData['token'],
    'password': password1,
  }, function(e){
      if(e['status'] === '00'){
          upgrade_rejection();
      }else{
          notif('danger', 'Authentication failed', e.message)
      }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function verifaccPassword(){
  $('#verifaccPassword').modal('show');
}

$('#verifaccPassword').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function verifrejPassword(){
  $('#verifrejPassword').modal('show');
}

$('#verifrejPassword').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function _users_request_append(data, i){
  // upgradeDetail(data.id_upgrade);
  $('#data_body').append(
    '<div onclick="upgradeDetail('+data.id_upgrade+')">' +
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
