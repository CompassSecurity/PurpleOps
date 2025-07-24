function showToast(message, state = 'success') {
  const toastEl = document.getElementById('toast');
  const toastBody = document.getElementById('toastBody');

  // Clear previous background/text color classes
  toastEl.classList.remove('bg-info', 'bg-danger', 'text-white');
  
  // Apply background and text color based on state
  if (state === 'error') {
    toastEl.classList.add('bg-danger', 'text-white');
  } else {
    toastEl.classList.add('bg-info', 'text-white'); // default is success
  }

  toastBody.textContent = message;

  const toast = new bootstrap.Toast(toastEl);
  toast.show();
}