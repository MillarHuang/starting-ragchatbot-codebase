/**
 * @jest-environment jsdom
 *
 * Frontend tests for script.js — covers initialization, message rendering,
 * sendMessage behaviour, XSS escaping, error handling, and UI interactions.
 */

const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

function setupDOM() {
  document.body.innerHTML = `
    <div id="chatMessages"></div>
    <input id="chatInput" />
    <button id="sendButton"></button>
    <span id="totalCourses"></span>
    <div id="courseTitles"></div>
    <button id="newChatBtn"></button>
    <div class="suggested-items">
      <button class="suggested-item" data-question="What is Python?">Python</button>
    </div>
  `;
}

function makeFetchMock(jsonOverrides = {}) {
  return jest.fn().mockResolvedValue({
    ok: true,
    json: () =>
      Promise.resolve({
        total_courses: 2,
        course_titles: ['Python Basics', 'JS Essentials'],
        ...jsonOverrides,
      }),
  });
}

async function loadScript() {
  jest.resetModules();
  global.marked = { parse: (text) => text };
  require('../script.js');
  document.dispatchEvent(new Event('DOMContentLoaded'));
  await flushPromises();
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------
describe('Initialization', () => {
  beforeEach(async () => {
    setupDOM();
    global.fetch = makeFetchMock();
    await loadScript();
  });

  test('displays welcome message on load', () => {
    expect(document.getElementById('chatMessages').textContent).toContain('Welcome');
  });

  test('fetches course stats on load', () => {
    expect(fetch).toHaveBeenCalledWith('/api/courses');
  });

  test('displays total course count', () => {
    expect(document.getElementById('totalCourses').textContent).toBe('2');
  });

  test('displays course titles in sidebar', () => {
    const courseTitles = document.getElementById('courseTitles');
    expect(courseTitles.innerHTML).toContain('Python Basics');
    expect(courseTitles.innerHTML).toContain('JS Essentials');
  });

  test('shows "No courses available" when list is empty', async () => {
    setupDOM();
    global.fetch = makeFetchMock({ total_courses: 0, course_titles: [] });
    await loadScript();
    expect(document.getElementById('courseTitles').innerHTML).toContain('No courses available');
  });
});

// ---------------------------------------------------------------------------
// Course stats — error handling
// ---------------------------------------------------------------------------
describe('Course stats error handling', () => {
  beforeEach(async () => {
    setupDOM();
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));
    await loadScript();
  });

  test('shows failure message when course stats fetch rejects', () => {
    expect(document.getElementById('courseTitles').innerHTML).toContain('Failed to load courses');
  });

  test('shows 0 for total courses on error', () => {
    expect(document.getElementById('totalCourses').textContent).toBe('0');
  });
});

// ---------------------------------------------------------------------------
// Message rendering
// ---------------------------------------------------------------------------
describe('Message rendering', () => {
  beforeEach(async () => {
    setupDOM();
    global.fetch = makeFetchMock();
    await loadScript();
  });

  test('user message text appears in chat immediately after send', () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: 'An answer', sources: [], session_id: 'abc' }),
    });

    document.getElementById('chatInput').value = 'What is recursion?';
    document.getElementById('sendButton').click();

    expect(document.getElementById('chatMessages').textContent).toContain('What is recursion?');
  });

  test('user message HTML is escaped to prevent XSS', () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('fail'));

    document.getElementById('chatInput').value = '<script>alert("xss")</script>';
    document.getElementById('sendButton').click();

    const html = document.getElementById('chatMessages').innerHTML;
    expect(html).not.toContain('<script>alert(');
    expect(html).toContain('&lt;script&gt;');
  });

  test('assistant answer is rendered after successful response', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          answer: 'Python is a high-level language.',
          sources: [],
          session_id: 'sess3',
        }),
    });

    document.getElementById('chatInput').value = 'What is Python?';
    document.getElementById('sendButton').click();
    await flushPromises();

    expect(document.getElementById('chatMessages').textContent).toContain(
      'Python is a high-level language.'
    );
  });

  test('sources section is rendered when sources are returned', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          answer: 'Some answer.',
          sources: ['<a href="#">Lesson 1</a>'],
          session_id: 'src-sess',
        }),
    });

    document.getElementById('chatInput').value = 'Tell me about lesson 1';
    document.getElementById('sendButton').click();
    await flushPromises();

    expect(document.getElementById('chatMessages').innerHTML).toContain('Sources');
    expect(document.getElementById('chatMessages').innerHTML).toContain('Lesson 1');
  });
});

// ---------------------------------------------------------------------------
// sendMessage behaviour
// ---------------------------------------------------------------------------
describe('sendMessage', () => {
  beforeEach(async () => {
    setupDOM();
    global.fetch = makeFetchMock();
    await loadScript();
  });

  test('sends POST to /api/query with the typed query', () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: 'ok', sources: [], session_id: 's1' }),
    });

    document.getElementById('chatInput').value = 'What is Python?';
    document.getElementById('sendButton').click();

    const queryCall = fetch.mock.calls.find((c) => c[0] === '/api/query');
    expect(queryCall).toBeDefined();
    expect(JSON.parse(queryCall[1].body).query).toBe('What is Python?');
  });

  test('does not call /api/query when input is empty', () => {
    global.fetch = jest.fn();

    document.getElementById('chatInput').value = '   ';
    document.getElementById('sendButton').click();

    const queryCalls = fetch.mock.calls.filter((c) => c[0] === '/api/query');
    expect(queryCalls.length).toBe(0);
  });

  test('clears the input field after sending', () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: 'response', sources: [], session_id: 's2' }),
    });

    const chatInput = document.getElementById('chatInput');
    chatInput.value = 'Hello?';
    document.getElementById('sendButton').click();

    expect(chatInput.value).toBe('');
  });

  test('shows error message when server returns non-ok response', async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false });

    document.getElementById('chatInput').value = 'Will this fail?';
    document.getElementById('sendButton').click();
    await flushPromises();

    expect(document.getElementById('chatMessages').textContent).toContain('Error');
  });

  test('sends message when Enter key is pressed', () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: 'response', sources: [], session_id: 's3' }),
    });

    const chatInput = document.getElementById('chatInput');
    chatInput.value = 'Enter test';
    chatInput.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter', bubbles: true }));

    const queryCall = fetch.mock.calls.find((c) => c[0] === '/api/query');
    expect(queryCall).toBeDefined();
    expect(JSON.parse(queryCall[1].body).query).toBe('Enter test');
  });
});

// ---------------------------------------------------------------------------
// New chat button
// ---------------------------------------------------------------------------
describe('New chat button', () => {
  beforeEach(async () => {
    setupDOM();
    global.fetch = makeFetchMock();
    await loadScript();
  });

  test('resets chat area and shows welcome message', async () => {
    // Send a message first so chat has content
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: 'hi', sources: [], session_id: 'old-session' }),
    });
    document.getElementById('chatInput').value = 'Hello';
    document.getElementById('sendButton').click();
    await flushPromises();

    // Click new chat
    global.fetch = jest.fn().mockResolvedValue({ ok: true });
    document.getElementById('newChatBtn').click();

    const messages = document.getElementById('chatMessages');
    expect(messages.textContent).toContain('Welcome');
  });
});

// ---------------------------------------------------------------------------
// Suggested questions
// ---------------------------------------------------------------------------
describe('Suggested questions', () => {
  beforeEach(async () => {
    setupDOM();
    global.fetch = makeFetchMock();
    await loadScript();
  });

  test('clicking a suggested question sends it as the query', () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: 'Python answer', sources: [], session_id: 's' }),
    });

    document.querySelector('.suggested-item').click();

    const queryCall = fetch.mock.calls.find((c) => c[0] === '/api/query');
    expect(queryCall).toBeDefined();
    expect(JSON.parse(queryCall[1].body).query).toBe('What is Python?');
  });
});
