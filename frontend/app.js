const form = document.querySelector('#task-form');
const taskList = document.querySelector('#task-list');
const taskCount = document.querySelector('#task-count');
const formPanel = document.querySelector('#form-panel');
const formTitle = document.querySelector('#form-title');
const formEyebrow = document.querySelector('#form-eyebrow');
const submitButton = document.querySelector('#submit-button');
const cancelEditButton = document.querySelector('#cancel-edit');
const formError = document.querySelector('#form-error');
const loadError = document.querySelector('#load-error');
const connectionStatus = document.querySelector('#connection-status');
let editingTaskId = null;

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers },
  });
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const payload = await response.json();
      if (payload.error) message = payload.error;
    } catch (_) {
      // Keep the status-based message when the server did not return JSON.
    }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function normalize(value) {
  return (value || '').trim().toLowerCase().replace(/\s+/g, '-');
}

function pretty(value, fallback) {
  return value ? value.replace(/[-_]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()) : fallback;
}

function makeBadge(value, kind, fallback) {
  const badge = document.createElement('span');
  const valueClass = normalize(value);
  badge.className = `badge ${kind}-${valueClass}`;
  badge.textContent = pretty(value, fallback);
  return badge;
}

function formatDeadline(value) {
  if (!value) return 'No deadline';
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
}

function buildTaskCard(task) {
  const card = document.createElement('article');
  card.className = 'task-card';

  const top = document.createElement('div');
  top.className = 'task-card-top';
  const title = document.createElement('h3');
  title.className = 'task-title';
  title.textContent = task.title;
  const actions = document.createElement('div');
  actions.className = 'task-actions';

  const edit = document.createElement('button');
  edit.className = 'task-action';
  edit.type = 'button';
  edit.dataset.action = 'edit';
  edit.dataset.id = task.id;
  edit.title = 'Edit task';
  edit.setAttribute('aria-label', `Edit ${task.title}`);
  edit.textContent = '✎';

  const remove = document.createElement('button');
  remove.className = 'task-action delete';
  remove.type = 'button';
  remove.dataset.action = 'delete';
  remove.dataset.id = task.id;
  remove.title = 'Delete task';
  remove.setAttribute('aria-label', `Delete ${task.title}`);
  remove.textContent = '×';
  actions.append(edit, remove);
  top.append(title, actions);

  const description = document.createElement('p');
  description.className = `task-description${task.description ? '' : ' empty'}`;
  description.textContent = task.description || 'No description added.';

  const meta = document.createElement('div');
  meta.className = 'task-meta';
  meta.append(makeBadge(task.status, 'status', 'No status'), makeBadge(task.priority, 'priority', 'No priority'));
  const deadline = document.createElement('span');
  deadline.className = 'deadline';
  deadline.textContent = `◷ ${formatDeadline(task.deadline)}`;
  if (task.deadline && task.deadline < new Date().toISOString().slice(0, 10) && normalize(task.status) !== 'done') {
    deadline.classList.add('overdue');
  }
  meta.append(deadline);
  card.append(top, description, meta);
  return card;
}

function renderTasks(tasks) {
  taskCount.textContent = tasks.length;
  taskList.replaceChildren();
  if (tasks.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    const icon = document.createElement('span');
    icon.className = 'empty-icon';
    icon.textContent = '✓';
    const message = document.createElement('strong');
    message.textContent = 'Your list is clear';
    const hint = document.createElement('span');
    hint.textContent = 'Add a task to get your study plan started.';
    empty.append(icon, message, hint);
    taskList.append(empty);
    return;
  }
  tasks.forEach((task) => taskList.append(buildTaskCard(task)));
}

async function loadTasks() {
  loadError.hidden = true;
  taskList.setAttribute('aria-busy', 'true');
  taskList.replaceChildren();
  const loading = document.createElement('div');
  loading.className = 'loading-state';
  const spinner = document.createElement('span');
  spinner.className = 'spinner';
  spinner.setAttribute('aria-hidden', 'true');
  loading.append(spinner, document.createTextNode('Loading tasks…'));
  taskList.append(loading);
  try {
    const tasks = await apiRequest('/tasks');
    if (!Array.isArray(tasks)) throw new Error('The API returned an unexpected task list.');
    connectionStatus.lastChild.textContent = ' API connected';
    connectionStatus.classList.remove('offline');
    renderTasks(tasks);
  } catch (error) {
    connectionStatus.lastChild.textContent = ' API unavailable';
    connectionStatus.classList.add('offline');
    taskCount.textContent = '—';
    taskList.replaceChildren();
    loadError.textContent = `${error.message} Check that the Flask API is running.`;
    loadError.hidden = false;
  } finally {
    taskList.setAttribute('aria-busy', 'false');
  }
}

function setEditing(task) {
  editingTaskId = task.id;
  form.elements.title.value = task.title || '';
  form.elements.description.value = task.description || '';
  form.elements.status.value = task.status || 'pending';
  form.elements.priority.value = task.priority || 'medium';
  form.elements.deadline.value = task.deadline || '';
  formTitle.textContent = 'Edit task';
  formEyebrow.textContent = 'MAKE AN UPDATE';
  submitButton.textContent = 'Save changes';
  cancelEditButton.hidden = false;
  formError.hidden = true;
  formPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  form.elements.title.focus({ preventScroll: true });
}

function resetForm() {
  editingTaskId = null;
  form.reset();
  form.elements.status.value = 'pending';
  form.elements.priority.value = 'medium';
  formTitle.textContent = 'Create a task';
  formEyebrow.textContent = 'GET STARTED';
  submitButton.textContent = 'Create task';
  cancelEditButton.hidden = true;
  formError.hidden = true;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  formError.hidden = true;
  const payload = Object.fromEntries(new FormData(form));
  for (const key of Object.keys(payload)) payload[key] = payload[key].trim() || null;
  if (!payload.title) {
    formError.textContent = 'Please enter a task title.';
    formError.hidden = false;
    form.elements.title.focus();
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = editingTaskId ? 'Saving…' : 'Creating…';
  try {
    if (editingTaskId) {
      await apiRequest(`/tasks/${editingTaskId}`, { method: 'PUT', body: JSON.stringify(payload) });
    } else {
      await apiRequest('/tasks', { method: 'POST', body: JSON.stringify(payload) });
    }
    resetForm();
    await loadTasks();
  } catch (error) {
    formError.textContent = error.message;
    formError.hidden = false;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = editingTaskId ? 'Save changes' : 'Create task';
  }
});

taskList.addEventListener('click', async (event) => {
  const button = event.target.closest('button[data-action]');
  if (!button) return;
  const taskId = Number(button.dataset.id);
  if (button.dataset.action === 'edit') {
    try {
      setEditing(await apiRequest(`/tasks/${taskId}`));
    } catch (error) {
      loadError.textContent = error.message;
      loadError.hidden = false;
    }
    return;
  }
  if (button.dataset.action === 'delete') {
    if (!window.confirm('Delete this task? This cannot be undone.')) return;
    button.disabled = true;
    try {
      await apiRequest(`/tasks/${taskId}`, { method: 'DELETE' });
      if (editingTaskId === taskId) resetForm();
      await loadTasks();
    } catch (error) {
      loadError.textContent = error.message;
      loadError.hidden = false;
      button.disabled = false;
    }
  }
});

document.querySelector('#refresh-button').addEventListener('click', loadTasks);
document.querySelector('#new-task-button').addEventListener('click', () => {
  resetForm();
  formPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
  form.elements.title.focus({ preventScroll: true });
});
cancelEditButton.addEventListener('click', resetForm);
loadTasks();
