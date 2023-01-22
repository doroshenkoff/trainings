var map = null
var line = null
var track = null
const mapScreen = document.querySelector('.map-screen')
const container = document.querySelector('.right-container')
const table = document.getElementById('laps')
const inputDate = document.getElementById('month')
const btnBreak = document.getElementById('break')


inputDate.addEventListener('input', (e) => {
    const date = e.target.value.split('-')
    const year = parseInt(date[0])
    const month = parseInt(date[1])
    console.log(year, month)
    getTrainings(year, month)
    
})

btnBreak.addEventListener('click', () => getTrainings())

const nav = document.querySelector('.nav')
window.addEventListener('scroll', () => {
    if (window.scrollY > nav.offsetHeight + 150) {
        nav.classList.add('active')
    } else {
        nav.classList.remove('active')
    }
})

const MONTHES = ['Январь', 'Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
const MONTHES2 = ['января', 'февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']

getTrainings()

mapScreen.addEventListener('dblclick', () => {
    mapScreen.classList.remove('active')
    map.remove()
    clearTable()
})


async function getTrainings(year=0, month=0) {
    container.innerHTML = ''
    var url = 'http://127.0.0.1:8000/tracks'
    if (year) {
        url = `http://127.0.0.1:8000/tracks/${year}/${month}`
    }
    
    res = await fetch(url, {mode: 'cors'})
    data = await res.json()
    fillRecords(data.records)
}


function fillRecords(data) {
    var firstDate = new Date(data[0].date)
    var div = appendMonthH1(firstDate)
    var totalKm = 0
    var totalTimes = 0

    data.forEach((item, idx) => {
        const {date, distance, total_time, average_speed, best_km, best_3km, best_5km, best_10km} = item
        const secondDate = new Date(date)
        if (secondDate.getMonth() !== firstDate.getMonth()) {
            appendMonthH1(firstDate, div, {km: totalKm, times: totalTimes})
            firstDate = secondDate
            div = appendMonthH1(firstDate)
            totalKm = 0
            totalTimes = 0
        }
        totalKm += distance
        totalTimes += 1
        if (idx == data.length - 1) {
            appendMonthH1(firstDate, div, {km: totalKm, times: totalTimes})
        }
        record = document.createElement('div')
        record.classList.add('record')
        record.innerHTML = `
            <h3 class="date">${parseDate(secondDate)}</h3>
            <h3 class="distance"><b>Distance:</b> ${distance} m</h3>
            <div class="record-data">
                <div class="info">
                    <p><b>Time:</b></p>
                    <p id="time">${parseTime(total_time)}</p>
                </div>
                <div class="info">
                    <p><b>Average Speed:</b></p>
                    <p id="speed">${parseTime(average_speed, false)}</p>
                </div>
                <div class="info">
                    <p><b>Best Lap:</b></p>
                    <p id="best-lap"> ${parseTime(best_km.speed, false)}</p>
                </div>
                ${best_3km.speed ? 
                    `<div class="info">
                        <p><b>Best 3 km:</b></p>
                        <p id="best-lap"> ${parseTime(best_3km.speed)}</p>
                    </div>` : ''
                }
                ${best_5km.speed ? 
                    `<div class="info">
                        <p><b>Best 5km:</b></p>
                        <p id="best-lap"> ${parseTime(best_5km.speed)}</p>
                    </div>` : ''
                }
                ${best_10km.speed ? 
                    `<div class="info">
                        <p><b>Best 10km:</b></p>
                        <p id="best-lap"> ${parseTime(best_10km.speed)}</p>
                    </div>` : ''
                }
            </div>  
        `
        record.addEventListener('click', () => {
            mapScreen.classList.add('active')
            mapScreen.style.top = `${window.visualViewport.pageTop + 30}px`
            getPoints(item)
            fillTable(item)
        })
        container.appendChild(record)
    })
}

function parseDate(date) {
    return `
        ${date.getDate()} ${MONTHES2[date.getMonth()]} ${date.getFullYear()}, 
        ${(date.getHours() + 2).toString().padStart(2, 0)}:${date.getMinutes().toString().padStart(2, 0)}
    `
}

function parseTime(time, h=true) {
    hours = Math.floor(time / 3600).toString()
    minutes = Math.floor((time - hours * 3600) / 60).toString()
    seconds = (time - hours * 3600 - minutes * 60).toString()
    if (h) {
        return `${hours.padStart(2, 0)}:${minutes.padStart(2, 0)}:${seconds.padStart(2, 0)}`
    } else {
        return `${minutes.padStart(2, 0)}'${seconds.padStart(2, 0)}''`
    } 
}

function appendMonthH1(date, div=null, params=null) {
    if (!div) {
        d = document.createElement('div')
        h = document.createElement('h2')
        d.classList.add('month')
        h.innerHTML = `
            ${MONTHES[date.getMonth()]} ${date.getFullYear()}
        `
        d.appendChild(h)
        container.appendChild(d)
        return d
    } else {
        t = document.createElement('table')
        t.innerHTML = `
            <tr><td>Количество пробежек:</td><td>${params.times}</tr>
            <tr><td>Всего:</td><td>${Math.round(params.km / 1000)} км</tr>
        `
        div.appendChild(t)
        return null
    }
}



async function getPoints(item) {
    url = `http://127.0.0.1:8000/track/points?id=${item._id}`
    token = localStorage.getItem('token')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    }
    res = await fetch(url, {headers: headers})
    if (res.status >= 400) {
        document.location.href = 'login/login.html'
    } else {
        track = await res.json()
        buildTrack(track, item)
        // getPlot(track.points)
    }
}


function buildTrack(data, item) {
    const points = data.points

    //initializing map
    map = L.map('map')
    map.setView(points[0], 13)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);

    //drawing a track    
    polyline = L.polyline(points, {color: 'blue'}).addTo(map)

    //drawing beginning and end of a track    
    L.circle(points[0], {
        color: 'green',
        fillColor: 'green',
        fillOpacity: 1,
        radius: 25,
    }).addTo(map)
    L.circle(points[points.length - 1], {
        color: 'red',
        fillColor: 'red',
        fillOpacity: 1,
        radius: 25,
    }).addTo(map)

    //centering track view on the map
    map.fitBounds(polyline.getBounds())

    //adding km markers to the track
    item.laps.forEach((lap, idx) => {
        L.marker(lap.point)
        .bindPopup(`${idx + 1} km`)
        .bindTooltip(`${idx + 1} km`, {
            permanent: true, 
            direction: 'right'
        })
        .addTo(map)
    })
}


function fillTable(item) {
    item.laps.forEach((lap, idx) => {
        const {total_time, temp, avg_speed} = lap
        const row = document.createElement('tr')
        if (idx === item.best_km.lap - 1) {
            row.classList.add('best')
        }
        if (temp === item.worst) {
            row.classList.add('worst')
        } 
        table.appendChild(row)
        const col_lap = document.createElement('td')
        col_lap.innerHTML = idx + 1
        const col_time = document.createElement('td')
        col_time.innerHTML = parseTime(total_time)
        const col_speed = document.createElement('td')
        col_speed.innerHTML = parseTime(temp, false)
        const col_avrg = document.createElement('td')
        col_avrg.innerHTML = parseTime(avg_speed, false)
        row.appendChild(col_lap)
        row.appendChild(col_time)
        row.appendChild(col_speed)
        row.appendChild(col_avrg)

        row.addEventListener('click', () => {
            if (line) {
                line.remove()
            }
            drawLine(lap)
        })
    })
}


function clearTable() {
    table.innerHTML = `
    <tr>
        <th>Km</th>
        <th>Time</th>
        <th>Speed</th>
        <th>Average Speed</th>
    </tr>
    `
}


function drawLine(lap) {
    const bgnPoint = Math.floor((lap.total_time - lap.temp) / 3)
    const endPoint = Math.floor(lap.total_time / 3) + 1

    line = L.polyline(track.points.slice(bgnPoint, endPoint), {color: 'red', weight: 6})
    line.addTo(map)
}

function getPlot(item) {
    TESTER = document.getElementById('tester')
    var trace = {
        y: item.map(point => point.hr),
        type: 'bar', 
    }
    var data = [trace]
    var layout = {
        showlegend: false,
    }
    Plotly.newPlot(TESTER, data, layout)
}


