let _page, _limit, _total_data;

function _request(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    _request_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

function _request_list(page){
  _loading(1);
  $.post('/api/v1/ams/request_log',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      _total_data = e.count_request.total_request;
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
      $('#data_body').empty();
      if(e.data.length > 0){
        for(i=0; i < e.data.length; i++){
          _request_append(e.data[i], i+1);
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
    _request_list(_page)
  }
}

// PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _request_list(_page)
  }
}

function _request_append(data, i){
  $('#data_body').append(
    '<tr>'+
    '<td>' + i + '</td>' +
    '<td>' + data.from_user_name + '</td>' +
    '<td>' + data.to_user_name + '</td>' +
    '<td>' + data.subject + '</td>' +
    '<td>' + data.description + '</td>' +
    '<td>' + data.amount + '</td>' +
    '<td>' + data.trx_status + '</td>' +
    '<td>' + data.added_time + '</td>' +
    '</tr>'+
    '</table>'
  )
}
