let _page, _limit, _total_data;

function _translog(){
  $(document).ready(function () {
    _page = 0;
    _limit = 25;
    _translog_list(_page);
    _loading(0);
    // $('#modalDetail').modal('show')
  });
}

function _translog_list(page){
  _loading(1);
  $.post('/api/v1/ams/trx_log',{
      'id': userData['id'],
      'token': userData['token'],
      'status': 0,
      'page': page,
      'skip': 0,
      'sector_id': $('#sector_id').val(),
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      // _total_data = e.count_request.total_request;
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
          _translog_append(e.data[i], i+1);
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
    _translog_list(_page)
  }
}

// PREVIOUS PAGE BUTTON
function _prev_page(){
  if(_page > 0){
    _page -= 1;
    _translog_list(_page)
  }
}

function _translog_append(data, i){
  $('#data_body').append(
    '<tr onclick="translog_detail_modal(\'' + data.id + '\')">'+
    '<td>' + i + '</td>' +
    // '<td>' + data.user_id + '</td>' +
    '<td>' + data.ref_id + '</td>' +
    '<td>' + data.user_name + '</td>' +
    '<td>' + data.user_phone + '</td>' +
    '<td>' + data.product_category_name + '</td>' +
    '<td>' + data.product_type_name + '</td>' +
    '<td>' + data.amount + '</td>' +
    '<td>' + data.date + '</td>' +
    '</tr>'+
    '</table>'
  )
}

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
