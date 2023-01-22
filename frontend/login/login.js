const labels = document.querySelectorAll('.form-control label')
const user = document.getElementById('user')
const pass = document.getElementById('password')
const btnLogin = document.querySelector('.btn')

labels.forEach((label) => {
    label.innerHTML = label.innerText.split('')
    .map((letter, idx) => `<span style="transition-delay: ${idx * 50}ms">${letter}</span>`)
    .join('')
})

btnLogin.addEventListener('click', (e) => {
    e.preventDefault()
    postData('http://127.0.0.1:8000/token', {
        username: user.value,
        password: pass.value
    })
})

async function postData(url, data = {}) {
    var formBody = []
    console.log(data)
    for (var property in data) {
        formBody.push(encodeURIComponent(property) + "=" + encodeURIComponent(data[property]))
        }
    formBody = formBody.join("&")
    
    const response = await fetch(url, {
      method: 'POST', // *GET, POST, PUT, DELETE, etc.
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formBody
    });
    if (response.status >= 400) {
        alert("Неправильный логин или пароль, чепушило!")
    } else {
        data = await response.json()
        updateToken(data.access_token)
        window.history.back()
    }
  }

  function updateToken(token) {
    localStorage.setItem('token', token)
  }