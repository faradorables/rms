function graph(){
  _loading(1);
  var selectyear = document.getElementById('selectYear');
  if (selectyear.value == "2019"){
        var year = 2019;
    }else if (selectyear.value == "2020"){
        var year = 2020;
    }else if (selectyear.value == "2021"){
        var year = 2021;
    }else if(selectyear.value == "2022"){
        var year = 2022;
    }

console.log(year)
  $.post('/api/v1/ams/dashboard',{
      'id': userData['id'],
      'token': userData['token'],
      'year' : year,
      'status': 0,
      'skip':0
  }, function (e) {
    let i;
    if(e['status'] === '00'){
      $('#new_user_month').text(e.new_user_month);
      $('#total_users').text(e.count_user.total_user);
      $('#total_wallet').text('Rp ' + e.total_wallet);
      $('#total_active_users').text(e.count_user.active_user);
      $('#data_body').empty();
      if(e.list.length > 0){
        for(i=0; i < 5; i++){
          _translog_append(e.list[i], i+1);
        }
      }else{
        $('#data_body').append(
          '<div class="_notif_menu"><i class="fa fa-exclamation-triangle"></i>User dari sektor ini belum tersedia.</div>'
        )
      }
      // console.log(month_count)
      let ctx_line = document.getElementById("myChart_line");
      let data = {
          labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Agt", "Sep", "Oct", "Nov", "Des"],
          datasets: [{
              label: 'Individual',
              data: [e.january, e.february, e.march, e.april, e.may, e.june, e.july, e.august, e.september, e.october, e.november, e.december],
              backgroundColor: 'transparent',
              borderColor: 'rgba(58, 43, 112, 1)',
              borderWidth: 2
          }, {
              label: 'Merchants',
              data: [0, 0, 0, 0, 0, 0],
              backgroundColor: 'transparent',
              borderColor: 'rgba(58, 43, 112, .5)',
              borderWidth: 2
          },{
              label: 'BUJT',
              data: [0, 0, 0, 0, 0, 0],
              backgroundColor: 'transparent',
              borderColor: 'rgba(23, 23, 80, .6)',
              borderWidth: 2
          }]
      };
      let myLineChart = new Chart(ctx_line, {
      type: 'line',
      data: data,
      options: {
          scales: {
              yAxes: [{
                  ticks: {
                      beginAtZero:true
                  }
              }]
          }
      }
      });
      let ctx_line_1 = document.getElementById("myChart_line_1");
      let data_1 = {
        labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Agt", "Sep", "Oct", "Nov", "Des"],
          datasets: [{
              label: 'Floating Money',
              data: [e.total_wallet_jan,
                e.total_wallet_feb,
                e.total_wallet_mar,
                e.total_wallet_apr,
                e.total_wallet_may,
                e.total_wallet_jun,
                e.total_wallet_jul,
                e.total_wallet_agt,
                e.total_wallet_sep,
                e.total_wallet_oct,
                e.total_wallet_nov,
                e.total_wallet_des],
              backgroundColor: 'rgba(58, 43, 112, .5)',
              borderColor: 'rgba(58, 43, 112, 1)',
              borderWidth: 2
          }]
      };
      let myLineChart_1 = new Chart(ctx_line_1, {
      type: 'line',
      data: data_1,
      options: {
          scales: {
              yAxes: [{
                  ticks: {
                      beginAtZero:true
                  }
              }]
          }
      }
      });
      var ctx = document.getElementById("myChart");
      var myChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Agt", "Sep", "Oct", "Nov", "Des"],
            datasets: [{
                label: 'Pulsa',
                data: [14, 21, 5, 7, 5, 8],
                backgroundColor: 'rgba(58, 43, 112, .5)',
                borderWidth: 1
            }, {
                label: 'PLN',
                data: [e.january, e.february, e.march, e.april, e.may, e.june, e.july, e.august, e.september, e.october, e.november, e.december],
                backgroundColor: 'rgba(58, 43, 112, 1)',
                borderWidth: 1
            },{
                label: 'OBU',
                data: [12, 93, 23, 31, 30,45],
                backgroundColor: 'rgba(23, 23, 80, 1)',
                borderWidth: 1
            }]
          },
          options: {
              scales: {
                  yAxes: [{
                      ticks: {
                          beginAtZero:true
                      },
                  }],
                  xAxes: [{
                      ticks: {
                          beginAtZero:true
                      },
                  }]
              }
          }
      });
    }else{
      notif('danger', 'System Error!', e.message);
    }
  }).fail(function(){
    notif('danger', 'System Error!', 'Mohon kontak IT Administrator');
  }).done(function(){
    _loading(0);
  });
}

function _translog_append(list, i){
  $('#data_body').append(
    // '<table class="table table-hover">'+
    '<tr onclick="translog_detail_modal(\'' + list.id + '\')">'+
    '<td>' + i + '</td>' +
    '<td>' + list.name + '</td>' +
    '<td>' + "Rp. " + list.amount + '</td>' +
    '<td>' + list.product_category_name + '</td>' +
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
