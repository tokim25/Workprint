const screens = [...document.querySelectorAll('.screen')];
const restartButton = document.getElementById('restartButton');
const evidenceDialog = document.getElementById('evidenceDialog');

function showScreen(name) {
  screens.forEach((screen) => {
    screen.classList.toggle('active', screen.dataset.screen === name);
  });
  restartButton.hidden = name === 'start';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.addEventListener('click', (event) => {
  const next = event.target.closest('[data-next]');
  const back = event.target.closest('[data-back]');
  if (next) showScreen(next.dataset.next);
  if (back) showScreen(back.dataset.back);
});

function restart() {
  document.querySelectorAll('.progress-list li').forEach((item) => {
    item.classList.remove('active', 'complete');
  });
  showScreen('start');
}

restartButton.addEventListener('click', restart);
document.getElementById('restartFromEnd').addEventListener('click', restart);

document.getElementById('investigateButton').addEventListener('click', () => {
  showScreen('investigating');
  const stages = [...document.querySelectorAll('.progress-list li')];

  stages.forEach((stage) => stage.classList.remove('active', 'complete'));

  stages.forEach((stage, index) => {
    window.setTimeout(() => {
      stages.forEach((item, itemIndex) => {
        item.classList.toggle('complete', itemIndex < index);
        item.classList.toggle('active', itemIndex === index);
      });
    }, 350 + index * 900);
  });

  window.setTimeout(() => {
    stages.forEach((item) => {
      item.classList.remove('active');
      item.classList.add('complete');
    });
    showScreen('discoveries');
  }, 3500);
});

document.getElementById('showEvidenceButton').addEventListener('click', () => {
  evidenceDialog.showModal();
});

document.querySelector('.dialog-close').addEventListener('click', () => {
  evidenceDialog.close();
});

evidenceDialog.addEventListener('click', (event) => {
  const bounds = evidenceDialog.getBoundingClientRect();
  const outside =
    event.clientX < bounds.left ||
    event.clientX > bounds.right ||
    event.clientY < bounds.top ||
    event.clientY > bounds.bottom;

  if (outside) evidenceDialog.close();
});
