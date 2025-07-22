function showToast(message) {
  const toastBody = document.getElementById('toastBody');
  toastBody.textContent = message;

  const toast = new bootstrap.Toast(document.getElementById('toast'));
  toast.show();
}