var SAVE_DELAY_MS = 600

function applyResult(section, result) {
  var drawing = section.querySelector('.drawing')
  var error = section.querySelector('.render-error')
  var status = section.querySelector('.status')
  if (result.svg) {
    drawing.innerHTML = result.svg
    drawing.classList.remove('stale')
    error.hidden = true
    error.textContent = ''
    status.textContent = 'Saved.'
    return
  }
  drawing.classList.add('stale')
  error.hidden = false
  error.textContent = result.error
  status.textContent = 'Saved, but PlantUML could not draw it.'
}

function save(section, source) {
  var status = section.querySelector('.status')
  status.textContent = 'Saving...'
  fetch('/api/diagram/' + section.dataset.type, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source: source }),
  })
    .then(function (response) {
      return response.json()
    })
    .then(function (result) {
      applyResult(section, result)
    })
    .catch(function () {
      status.textContent = 'Not saved: the page server stopped. Run the skill again to restart it.'
    })
}

function watch(section) {
  var editor = section.querySelector('textarea')
  var timer = null
  editor.addEventListener('input', function () {
    clearTimeout(timer)
    timer = setTimeout(function () {
      save(section, editor.value)
    }, SAVE_DELAY_MS)
  })
}

document.querySelectorAll('section.diagram[data-editable]').forEach(watch)
