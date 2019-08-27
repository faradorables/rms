let _page, _limit, _total_data;
// var show;
$('input#view_pass').on('change', function () {
    if ($(this).is(':checked')) {
        $('input#password').attr('type', 'text');
    }else{
        $('input#password').attr('type', 'password');
    }
})

function _obu(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    showBy();
    _loading(0);
  });
}

function showBy() {
  var show = document.getElementById("showBy");
  if (show.value == "all"){
        _obu_list(_page);
    }else if (show.value == "owned"){
      _obu_list_owned(_page);
    }else if (show.value == "active"){
      _obu_list_active(_page);
    }else if(show.value == "nonactive"){
      _obu_list_nonactive(_page);
    }
    console.log(_page)
}

// ========================================================
// obu LIST
// ========================================================

// CALL THE obu
function _obu_list(page){
  _loading(1);
  $.post('/api/v1/ams/obu',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_obu.total_obu;
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
      $('.total_data').text(_total_data);
      $('#total_obu').text(e.count_obu.total_obu);
      $('#total_active_obu').text(e.count_obu.active_obu);
      $('#user_owned').text(e.count_obu.user_owned);
      $('#non_active_obu').text(e.count_obu.non_active_obu);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _obu_append(e.data[i], i+1);
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

// LIST OWNED OBU
function _obu_list_owned(page){
  _loading(1);
  $.post('/api/v1/ams/obu_show_owned',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_obu.user_owned;
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
      $('.total_data').text(_total_data);
      $('#total_obu').text(e.count_obu.total_obu);
      $('#total_active_obu').text(e.count_obu.active_obu);
      $('#user_owned').text(e.count_obu.user_owned);
      $('#non_active_obu').text(e.count_obu.non_active_obu);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _obu_append(e.data[i], i+1);
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
// OBU LIST ACTIVE
function _obu_list_active(page){
  _loading(1);
  $.post('/api/v1/ams/obu_active',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_obu.active_obu;
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
      $('.total_data').text(_total_data);
      $('#total_obu').text(e.count_obu.total_obu);
      $('#total_active_obu').text(e.count_obu.active_obu);
      $('#user_owned').text(e.count_obu.user_owned);
      $('#non_active_obu').text(e.count_obu.non_active_obu);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _obu_append(e.data[i], i+1);
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

//OBU LIST NONACTIVE
function _obu_list_nonactive(page){
  _loading(1);
  $.post('/api/v1/ams/obu_nonactive',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_obu.non_active_obu;
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
      $('.total_data').text(_total_data);
      $('#total_obu').text(e.count_obu.total_obu);
      $('#total_active_obu').text(e.count_obu.active_obu);
      $('#user_owned').text(e.count_obu.user_owned);
      $('#non_active_obu').text(e.count_obu.non_active_obu);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _obu_append(e.data[i], i+1);
          console.log(e.detail)
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
    _obu_list(_page)
  }
}

// PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _obu_list(_page)
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

// APPENDING THE obu
function _obu_append(data, i){
  const user = '-'
  if(data.user === {}){
    user = data.user.name;
  }
  $('#data_body').append(
    '<div>' +
    '<div onclick="obuDetail('+data.id+')" class="id">' + i + '</div>' +
    '<div onclick="obuDetail('+data.id+')" class="name">' + data.uid + '</div>' +
    '<div onclick="obuDetail('+data.id+')" class="email">' + data.user.name + '</div>' +
    '<div class="option">' +
    '<a><i class="fa fa-exclamation-triangle"></i></a>' +
    '<a><i class="fa fa-star"></i></a>' +
    '<a onclick="delete_obu('+data.id+')"><i class="fa fa-trash"></i></a>' +
    '</div>' +
    '</div>'
  )
}

// APPENDING THE ROLE
function _role_append(data){
  $('#_obu_roles, #_edit_obu_roles').append(
    '<option value="' + data.id + '">' + data.name + '</option>'
  )
}

// DELETE MODAL
function _delete_obu_modal(id){
  $('#_delete_obu_id').val(id);
  $('#modalDeleteobu').modal('show');
}

function _submit_obu_delete(){
  $.post('/api/v1/ams/obu',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 4,
      'sector_id': $('#sector_id').val(),
      '_id': $('#_delete_obu_id').val(),
  }, function (e) {
      if(e.status === '00'){
        $('._obu_data_' + $('#_delete_obu_id').val()).remove()
      }else{
        notif('danger', 'System Error!', e.message);
      }
      $('#modalDeleteobu').modal('hide');
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  });
}

function obuDetail(obu_id){
  _loading(1);
  $.post('/api/v1/ams/obudetail',{
      'id_admin': userData['id'],
      'token': userData['token'],
      'status': 0,
      'obu_id': obu_id,
  }, function (e) {
    let i;
      if(e['status'] === '00'){
        $('#detail_id').text(e.detail.user_id);
        $('#detail_name').text(e.detail.name);
        $('#detail_phone').text(e.detail.phone);
        $('#detail_email').text(e.detail.email);
        $('#user_total_wallet').text('Rp ' + e.detail.wallet);
        $('#user_total_obu').text(+ e.detail.total_obu);
        $('#data_body2').empty();
        if(e.data.length > 0){
          for(i=0; i < e.data.length; i++){
            _obu_detail_append(e.data[i], i+1);
            console.log(e)
          }
        }else{
          $('#data_body2').append(
            '<div class="_notif_menu"><i class="fa fa-exclamation-triangle"></i>admin dari sektor ini belum tersedia.</div>'
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

  $('#obuDetail').modal('show');
  console.log(obu_id);
}

$('#obuDetail').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function _obu_detail_append(data){
  $('#data_body2').append(
    '<div onclick="obuUnitDetail('+data.obu_id+')">' +
    '<div class="id">' + data.obu_uid + '</div>' +
    '<div class="name">' + data.plate_id + '</div>' +
    '<div class="option">' +
    '<a><i class="fa fa-exclamation-triangle"></i></a>' +
    '<a><i class="fa fa-star"></i></a>' +
    '<a><i class="fa fa-trash"></i></a>' +
    '</div>' +
    '</div>'
  )
  console.log(data.obu_id)
}

function obuUnitDetail(obu_id){
  _loading(1);
  $.post('/api/v1/ams/obuunitdetail',{
      'id_admin': userData['id'],
      'token': userData['token'],
      'status': 0,
      'obu_id': obu_id,
  }, function (e) {
    let i;
      if(e['status'] === '00'){
        document.getElementById("back_plate").src= e.data.back_plate;
        document.getElementById("back_vehicle").src= e.data.back_vehicle;
        document.getElementById("front_plate").src=e.data.front_plate;
        document.getElementById("front_vehicle").src= e.data.front_vehicle;
        $('#vehicle_type').text(e.data.vehicle_type_name);
        $('#vehicle_brand').text(e.data.vehicle_brand_name);
        $('#vehicle_series').text(e.data.vehicle_series_name);
        $('#vehicle_model').text(e.data.vehicle_model_name);
        $('#vehicle_color').text(e.data.vehicle_color_name);
        $('#detail_id').text(e.data.obu_id);
        $('#plate_id').text(e.data.plate_id);
      }else{
        notif('danger', 'System Error!', e.message);
      }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });

  $('#obuUnitDetail').modal('show');
  console.log(obu_id);
}

$('#obuUnitDetail').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function obuForm(){
  $('#obuForm').modal('show');
}

$('#obuForm').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function obuPassword(){
  $('#obuPassword').modal('show');
}

$('#obuPassword').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function add_obu(){
  var uid = document.getElementById("uid").value;
  var pin = document.getElementById("pin").value;
//   var text = new Blob([''], { type: "text/plain"})
//   var formData = new FormData();
//   formData.append('id', text, userData['id']);
//   formData.append('token', text, userData['token']);
//   formData.append('excel', $('input[type=file]')[0].files[0]);
//
//   _loading(1);
//   $.ajax({
//     url: '/api/v1/add_obu',
//     data: formData,
//     type: 'POST',
//     contentType: false, // NEEDED, DON'T OMIT THIS (requires jQuery 1.6+)
//     processData: false, // NEEDED, DON'T OMIT THIS
//     success: function(e){
//       notif('success', 'Success!', e['messages']);
//     },
//     error:function(e){
//         notif('danger', 'System Error!', e['messages']);
//     },
//     // ... Other options like success and etc
// });
  _loading(1);
  $.post('/api/v1/add_obu',{
      'id': userData['id'],
      'token': userData['token'],
      'uid': uid,
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
    _loading(0);
    _obu_list(_page);
  });

}

function delete_obu(id){
  _loading(1);
  $.post('/api/v1/delete_obu',{
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
    showBy();
  });
}

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
          obuForm();
      }else{
          notif('danger', 'Authentication failed', e.message)
      }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}
