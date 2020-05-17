function plotLineChart(plot_params,plotID) {
    
    console.log(plot_params['x_axis']);
    var ctx = document.getElementById(plotID);
    var myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: plot_params['x_axis'],
        datasets: [
        { 
            data: plot_params['y_axis']
        }
        ]
    }
    });
}