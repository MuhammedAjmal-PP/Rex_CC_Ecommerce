/**
 * REX CC Admin Dashboard — Chart & Filter Logic
 * Uses Chart.js 4.x + Axios (loaded in base_admin.html)
 */

(function () {
    'use strict';

    let chartInstance = null;
    const ctx = document.getElementById('revenueChart').getContext('2d');

    // ── Gradient fills ──
    function makeGradient(color1, color2) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 350);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        return gradient;
    }

    // ── Progressive Animation ──
    const totalDuration = 2000;
    const delayBetweenPoints = totalDuration / 12; // roughly dividing based on max data points
    const previousY = (ctx) => ctx.index === 0 ? ctx.chart.scales.y.getPixelForValue(100) : ctx.chart.getDatasetMeta(ctx.datasetIndex).data[ctx.index - 1].getProps(['y'], true).y;
    
    const animation = {
        x: {
            type: 'number',
            easing: 'linear',
            duration: delayBetweenPoints,
            from: NaN, // the point is initially skipped
            delay(ctx) {
                if (ctx.type !== 'data' || ctx.xStarted) {
                    return 0;
                }
                ctx.xStarted = true;
                return ctx.index * delayBetweenPoints;
            }
        },
        y: {
            type: 'number',
            easing: 'linear',
            duration: delayBetweenPoints,
            from: previousY,
            delay(ctx) {
                if (ctx.type !== 'data' || ctx.yStarted) {
                    return 0;
                }
                ctx.yStarted = true;
                return ctx.index * delayBetweenPoints;
            }
        }
    };

    // ── Render / update chart ──
    function renderChart(data) {
        if (chartInstance) {
            chartInstance.destroy();
        }

        const revenueGradient = makeGradient('rgba(102, 126, 234, 0.25)', 'rgba(102, 126, 234, 0.02)');
        const ordersGradient = makeGradient('rgba(245, 87, 108, 0.25)', 'rgba(245, 87, 108, 0.02)');

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Revenue (₹)',
                        data: data.revenue,
                        backgroundColor: revenueGradient,
                        borderColor: '#667eea',
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        borderWidth: 2.5,
                        tension: 0.35,
                        fill: true,
                        yAxisID: 'y',
                        order: 2,
                    },
                    {
                        label: 'Orders',
                        data: data.orders,
                        borderColor: '#f5576c',
                        backgroundColor: ordersGradient,
                        pointBackgroundColor: '#f5576c',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        borderWidth: 2.5,
                        tension: 0.35,
                        fill: true,
                        yAxisID: 'y1',
                        order: 1,
                    },
                ],
            },
            options: {
                animation,
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 20,
                            font: { family: 'Montserrat', size: 12, weight: '500' },
                        },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.85)',
                        titleFont: { family: 'Montserrat', size: 13 },
                        bodyFont: { family: 'Montserrat', size: 12 },
                        padding: 14,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (tooltipItem) {
                                if (tooltipItem.dataset.yAxisID === 'y') {
                                    return ` Revenue: ₹${tooltipItem.raw.toLocaleString('en-IN')}`;
                                }
                                return ` Orders: ${tooltipItem.raw}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            font: { family: 'Montserrat', size: 11 },
                            color: '#888',
                        },
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        grid: { color: 'rgba(0, 0, 0, 0.04)' },
                        title: {
                            display: true,
                            text: 'Revenue (₹)',
                            font: { family: 'Montserrat', size: 12, weight: '500' },
                            color: '#667eea',
                        },
                        ticks: {
                            font: { family: 'Montserrat', size: 11 },
                            color: '#888',
                            callback: function (value) {
                                if (value >= 1000) return '₹' + (value / 1000).toFixed(1) + 'K';
                                return '₹' + value;
                            },
                        },
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        title: {
                            display: true,
                            text: 'Orders',
                            font: { family: 'Montserrat', size: 12, weight: '500' },
                            color: '#f5576c',
                        },
                        ticks: {
                            font: { family: 'Montserrat', size: 11 },
                            color: '#888',
                            stepSize: 1,
                        },
                    },
                },
            },
        });
    }

    // ── Fetch data from API ──
    function fetchChartData(filter) {
        axios
            .get(CHART_DATA_URL, { params: { filter: filter } })
            .then(function (response) {
                renderChart(response.data);
            })
            .catch(function (error) {
                console.error('Failed to load chart data:', error);
            });
    }

    // ── Filter button handling ──
    const filterBtns = document.querySelectorAll('.chart-filter-btn');
    filterBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            filterBtns.forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');
            fetchChartData(btn.dataset.filter);
        });
    });

    // ── Initial load ──
    fetchChartData('monthly');
})();
