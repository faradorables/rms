let _page, _limit, _total_data;
var plaza_id;

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
    _plaza_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

// ========================================================
// users LIST
// ========================================================

// CALL THE users
function _plaza_list(page){
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
      _total_data = e.count_user.total_plaza;
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
      $('#total_trx').text(+ e.total_trx.client_trx);
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _plaza_append(e.data[i], i+1);
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
    _plaza_list(_page)
  }
}

// PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _plaza_list(_page)
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

function _plaza_lane(id){
  $.post('/api/v1/ams/lane',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'plaza_id': id,
      'skip':0
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      $('#data_lane').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _lane_append(e.data[i], i+1);
        }
        for(i=0; i < e.data.length; i++){
          _lane_all_append(e.data[i], i+1);
        }
      }else{
        $('#data_lane').append(
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

// APPENDING THE users
function _plaza_append(data, i){
  $('#data_body').append(
    '<div onclick="modalDetail('+data.plaza_id+')">' +
    '<div class="no">' + i + '</div>' +
    '<div class="name">' + data.name + '</div>' +
    '<div class="address">' + data.address + '</div>' +
    '<div class="latitude">' + data.latitude + '</div>' +
    '<div class="longitude">' + data.longitude + '</div>' +
    '<div class="option">' +
    '<a><i class="fas fa-info-circle"></i></a>' +
    '<a><i class="fas fa-ban"></i></a>' +
    '</div>' +
    '</div>'
  )
}

function _lane_append(data, i){
  $('#data_lane').append(
    '<tr>'+
    '<td>' + i + '</td>' +
    '<td>' + data.lane_name + '</td>' +
    '<td>' + data.lane_type + '</td>' +
    '</tr>'+
    '</table>'
  )
}

function _lane_all_append(data, i){
  $('#data_lane_all').append(
    '<tr>'+
    '<td>' + i + '</td>' +
    '<td>' + data.lane_name + '</td>' +
    '<td>' + data.lane_type + '</td>' +
    '</tr>'+
    '</table>'
  )
}

function modalDetail(id){
  console.log(id)
  _loading(1);
  $.post('/api/v1/ams/userdetail',{
      'id_admin': userData['id'],
      'token': userData['token'],
      'status': 0,
      'plaza_id': id,
  }, function (e) {
    let i;
      if(e['status'] === '00'){
        if (id > 0){
          _plaza_lane(id);
          plaza_id = id;
          $('#detail_name').text(e.id.name);
          $('#detail_address').text(e.id.address);
          $('#detail_client').text(e.id.client);
          $('#total_lane').text(e.id.total_lane);
          $('#user_total_obu').text(+ e.id.total_obu);
          $('#user_total_trx').text('Rp ' + e.id.user_trx);
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

function lane_all_modal(){
  $('#laneallmodal').modal('show');
}

$('#laneallmodal').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function translog_detail_modal(_id){
_loading(1);
$.post('/api/v1/ams/trx_log',{
    'id': userData['id'],
    'token': userData['token'],
    'status': 1,
    '_id': _id
}, function (e) {
  let i;
    if(e['status'] === '00'){
      $('#user_id').text(e.data.user_id);
      $('#name').text(e.data.name);
      $('#type_name').text(e.data.type_name);
      $('#amount').text('Rp.'+e.data.amount);
      $('#date').text(e.data.date);
      $('#uid').text(e.data.uid);
      $('#product_category_name').text(e.data.product_category_name);
      $('#product_detail_name').text(e.data.product_detail_name);
      $('#product_type_name').text(e.data.product_type_name);
      $('#provider').text(e.data.provider);
      $('#ref_id').text(e.data.ref_id);
      $('#refca').text(e.data.refca);
      $('#refsb').text(e.data.refsb);
      $('#serialno').text(e.data.serialno);
      console.log(e);
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

function formPassword(){
  $('#formPassword').modal('show');
}

$('#formPassword').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function redirect_to_form() {
  var pin = document.getElementById("pin").value;
  _loading(1);
  $.post('/api/v1/auth/verif_pin',{
    'id': userData['id'],
    'token': userData['token'],
    'pin': pin
  }, function(e){
    console.log(userData['id']);
      if(e['status'] === '00'){
          addPlazaForm();
      }else{
          notif('danger', 'Authentication failed', e.message)
      }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function addPlazaForm(){
  $('#addPlazaForm').modal('show');
}

$('#addPlazaForm').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function add_plaza(){
  var name = document.getElementById("name").value;
  var address = document.getElementById("address").value;
  var image = document.getElementById("image").value;
  var latitude = document.getElementById("latitude").value;
  var longitude = document.getElementById("longitude").value;

  _loading(1);
  $.post('/api/v1/add_plaza',{
      'id': userData['id'],
      'token': userData['token'],
      'name': name,
      'address': address,
      'image': image,
      'latitude': latitude,
      'longitude': longitude
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
    _plaza_list(_page);
  });
}

function addLaneForm(){
  $('#addLaneForm').modal('show');
  _lanetype_list();
}

$('#addLaneForm').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function _lanetype_list(){
  _loading(1);
  $.post('/api/v1/ams/lanetype',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _lanetype_append(e.data[i], i);
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

function _lanetype_append(data){
  $('#role_body').append(
    '<option value="'+ data.id +'">'+ data.name +'</option>'
  )
}

function add_lane(){
  var name = document.getElementById("lane_name").value;
  var type = document.getElementById("role_body").value;

  _loading(1);
  $.post('/api/v1/add_lane',{
      'id': userData['id'],
      'token': userData['token'],
      'name': name,
      'lanetype': type,
      'plaza_id': plaza_id

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
    _plaza_lane(plaza_id);
  });

}
