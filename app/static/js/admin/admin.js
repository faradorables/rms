let _page, _limit, _total_data;

function _admins(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    _admins_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

// ========================================================
// admins LIST
// ========================================================

// CALL THE admins
function _admins_list(page){
  _loading(1);
  $.post('/api/v1/ams/admin',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_admin.total_admins;
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
      $('#total_admins, .total_data').text(_total_data);
      $('#total_active_admins').text(e.count_admin.active_admins);
      $('#total_passive_admins').text(e.count_admin.passive_admins);
      $('#total_wallet').text('Rp ' + e.total_wallet);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _admins_append(e.data[i], i+1);
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
//
// // NEXT PAGE BUTTON
function _next_page(){
  if((_page + 1)*25<_total_data){
    _page += 1;
    _admins_list(_page)
  }
}

// // PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _admins_list(_page)
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

// APPENDING THE admins
function _admins_append(data, i){
  $('#data_body').append(
    '<div>' +
    '<div onclick="modalDetail('+data.id+')" class="id">' + i + '</div>' +
    '<div onclick="modalDetail('+data.id+')"><div class="profilePicture"></div></div>' +
    '<div onclick="modalDetail('+data.id+')" class="name">' + data.name + '</div>' +// console.log(i);
    '<div onclick="modalDetail('+data.id+')" class="email">' + data.email + '</div>' +
    '<div onclick="modalDetail('+data.id+')" class="phone">' + data.phone + '</div>' +
    // '<div onclick="modalDetail('+data.id+')" class="role"> ' + data.role_id + '</div>' +
    '<div onclick="modalDetail('+data.id+')" class="rolename"> ' + data.role_name + '</div>' +
    '<div class="option">' +
    '<a onclick="modalDetail('+data.id+')"><i class="fas fa-info-circle"></i></a>' +
    '<a><i class="fas fa-key"></i></a>' +
    '<a onclick="delete_admin('+data.id+')"><i class="fas fa-trash"></i></a>' +
    '</div>' +
    '</div>'
  )
}

// appending roles of admin
function _roles_append(data){
  $('#role_body').append(
    '<option value="'+ data.id +'">'+ data.name +'</option>'
  )
  $('#role_body2').append(
    '<option value="'+ data.id +'">'+ data.name + '</option>'
  )
}

// modal admin detail based on id
function modalDetail(id){
  _loading(1);
  $.post('/api/v1/ams/detail',{
      'id_admin': userData['id'],
      'token': userData['token'],
      'status': 0,
      'id': id,
  }, function (e) {
    let i;
      if(e['status'] === '00'){
        if (id > 0){
          $('#detail_id').text(e.id.id);
          $('#detail_name').text(e.id.name);
          $('#detail_phone').text(e.id.phone);
          $('#detail_email').text(e.id.email);
          $('#detail_role_id').text(e.id.role_id);
          $('#detail_role_name').text(e.id.role_name);
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
  console.log(id);
}

$('#modalDetail').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

// modal for add admin form
function adminForm(){
  $('#adminForm').modal('show');
  _roles_list();
}

$('#adminForm').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

// list of admin roles
function _roles_list(){
  _loading(1);
  $.post('/api/v1/ams/role',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _roles_append(e.data[i], i);
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

// function of adding admin
function add_admin(){
  var name = document.getElementById("name").value;
  var email = document.getElementById("email").value;
  var phone = document.getElementById("phone").value;
  var pin = document.getElementById("pin").value;
  var role = document.getElementById("role_body").value;
  var password = document.getElementById("password").value;

  _loading(1);
  $.post('/api/v1/add_admin',{
      'id': userData['id'],
      'token': userData['token'],
      'name': name,
      'email': email,
      'phone': phone,
      'pin': pin,
      'role': role,
      'password': password
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
    _admins_list(_page);
  });

  console.log(name);
  console.log(email);
  console.log(phone);
  console.log(role);
  console.log("oit")
}

// modal of edit admin form
function editForm(id){
  $('#editForm').modal('show');
  console.log(id)
  _roles_list();
  document.getElementById("name2").value = document.getElementById('detail_name').innerHTML;
  document.getElementById("email2").value = document.getElementById('detail_email').innerHTML;
  document.getElementById("phone2").value = document.getElementById('detail_phone').innerHTML;
  document.getElementById("role_body2").value = document.getElementById('detail_role_id').innerHTML;
}

$('#editForm').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

// function of editing admin
function edit_admin(){
  var name = document.getElementById("name2").value;
  var email = document.getElementById("email2").value;
  var phone = document.getElementById("phone2").value;
  var role = document.getElementById("role_body2").value;
  var user_id = document.getElementById('detail_id').innerHTML;

  _loading(1);
  $.post('/api/v1/edit_admin',{
      'id_admin': userData['id'],
      'token': userData['token'],
      'user_id':user_id,
      'name': name,
      'email': email,
      'phone': phone,
      'role': role,
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
    _admins_list(_page);
  });
}

function delete_admin(id){
  _loading(1);
  $.post('/api/v1/delete_admin',{
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
    _admins_list(_page);
  });
}
