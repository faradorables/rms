let _page, _limit, _total_data;
var price_id;

function _users(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    _pricing_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

// ========================================================
// users LIST
// ========================================================

// CALL THE users
function _pricing_list(page){
  _loading(1);
  $.post('/api/v1/ams/pricing',{
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
          _pricing_append(e.data[i], i+1);
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

function _pricing_append(data, i){
  $('#data_body').append(
    '<tr>'+
    '<td>' + i + '</td>' +
    '<td>' + data.plaza_in + '</td>' +
    '<td>' + data.plaza_out + '</td>' +
    '<td>'+"Golongan " + data.vehicle_class + '</td>' +
    '<td>'+"Rp." + data.price + '</td>' +
    '<td>'+
    '<a onclick="editPrice('+data.id+')"><i class="fas fa-edit"></i></a>' +
    '<a><i class="fas fa-ban"></i></a>' +
    '</td>'+
    '</tr>'+
    '</table>'
  )
}

function addpriceForm(){
  _loading(0);
  _plaza_list();
  _vehicle_list();
  $('#addpriceForm').modal('show');
}

$('#addpriceForm').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function pricePassword(){
  _loading(0);
  $('#pricePassword').modal('show');
}

$('#pricePassword').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function redirect_to_form() {
  var password = document.getElementById("password").value;
  _loading(1);
  $.post('/api/v1/auth/verif_pin',{
    'id': userData['id'],
    'token': userData['token'],
    'pin': password
  }, function(e){
    console.log(userData['id']);
      if(e['status'] === '00'){
          add_price();
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

function redirect_to_form2() {
  var password = document.getElementById("password").value;
  _loading(1);
  $.post('/api/v1/auth/verif_pin',{
    'id': userData['id'],
    'token': userData['token'],
    'pin': password
  }, function(e){
    console.log(userData['id']);
      if(e['status'] === '00'){
          edit_price();
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

function _plaza_list(){
  _loading(1);
  $.post('/api/v1/ams/list_plaza',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _plazalist_append(e.data[i], i);
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

function _plazalist_append(data){
  $('#plaza_in').append(
    '<option value="'+ data.plaza_id +'">'+ data.name +'</option>'
  )
  $('#plaza_out').append(
    '<option value="'+ data.plaza_id +'">'+ data.name +'</option>'
  )
}

function _vehicle_list(){
  _loading(1);
  $.post('/api/v1/ams/vehicle_class',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _vehiclelist_append(e.data[i], i);
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

function _vehiclelist_append(data){
  $('#vehicle_class').append(
    '<option value="'+ data.id +'">'+ data.name +'</option>'
  )
}

function add_price(){
  var plaza_in = document.getElementById("plaza_in").value;
  var plaza_out = document.getElementById("plaza_out").value;
  var vehicle_class = document.getElementById("vehicle_class").value;
  var price = document.getElementById("price").value;
  _loading(1);
  $.post('/api/v1/add_price',{
      'id': userData['id'],
      'token': userData['token'],
      'plaza_in_id': plaza_in,
      'plaza_out_id': plaza_out,
      'vehicle_class_id': vehicle_class,
      'price': price

  }, function (e) {
    if(e['status'] === '00'){
      console.log(e['messages'])
      nav_href('pricing');
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

function editPrice(id){
  _loading(1);
  _plaza_list();
  _vehicle_list()
  $('#editPrice').modal('show');
  $.post('/api/v1/ams/pricedetail',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'price_id': id,
  }, function (e) {
    let i;
      if(e['status'] === '00'){
        if (id > 0){
          document.getElementById("plaza_in").value = e.id.plaza_in_id;
          document.getElementById("plaza_out").value = e.id.plaza_out_id;
          document.getElementById("vehicle_class").value = e.id.vehicle_class;
          document.getElementById("price2").value = e.id.price;
          price_id = id;
          console.log(id)
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
}

$('#editPrice').on('shown.bs.modal', function () {
  $(this).css({'padding': '0'})
})

function edit_price(){
  var plaza_in = document.getElementById("plaza_in").value;
  var plaza_out = document.getElementById("plaza_out").value;
  var vehicle_class = document.getElementById("vehicle_class").value;
  var price = document.getElementById("price2").value;
  _loading(1);
  $.post('/api/v1/edit_price',{
      'id': userData['id'],
      'token': userData['token'],
      'plaza_in': plaza_in,
      'plaza_out': plaza_out,
      'vehicle_class': vehicle_class,
      'price': price,
      'price_id': price_id

  }, function (e) {
    if(e['status'] === '00'){
      console.log(e['messages'])
      _pricing_list(_page);
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
