let _page, _limit, _total_data;
var plaza_id;

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
    '<a><i class="fas fa-info-circle"></i></a>' +
    '<a><i class="fas fa-ban"></i></a>' +
    '</td>'+
    '</tr>'+
    '</table>'
  )
}
