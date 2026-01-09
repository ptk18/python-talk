/**
 * Main Application Logic
 * Ties together the turtle graphics, introspection, and UI
 * Now with async backend API calls for real Python introspection
 */

(function() {
  // DOM Elements
  const codeEditor = document.getElementById('code-editor');
  const methodsPanel = document.getElementById('methods-panel');
  const moduleStatus = document.getElementById('module-status');
  const commandInput = document.getElementById('command-input');
  const runBtn = document.getElementById('run-btn');
  const clearBtn = document.getElementById('clear-btn');
  const resetBtn = document.getElementById('reset-btn');
  const outputDiv = document.getElementById('output');
  const canvas = document.getElementById('turtle-canvas');

  // Initialize turtle
  let turtle = new Turtle(canvas);

  // Track detected imports and their aliases
  let currentImports = [];
  let moduleAliases = {}; // e.g., { 't': 'turtle' }
  let isLoading = false;

  /**
   * Show loading state in methods panel
   */
  function showLoading() {
    isLoading = true;
    methodsPanel.innerHTML = `
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <p>Introspecting modules...</p>
      </div>
    `;
    moduleStatus.textContent = 'Loading...';
    moduleStatus.classList.remove('active');
    moduleStatus.classList.add('loading');
  }

  /**
   * Hide loading state
   */
  function hideLoading() {
    isLoading = false;
    moduleStatus.classList.remove('loading');
  }

  /**
   * Show error state in methods panel
   */
  function showError(message) {
    methodsPanel.innerHTML = `
      <div class="error-state">
        <p class="error-message">${message}</p>
        <p class="error-hint">Make sure the server is running: <code>python server.py</code></p>
      </div>
    `;
    moduleStatus.textContent = 'Error';
    moduleStatus.classList.remove('active');
    moduleStatus.classList.add('error');
  }

  /**
   * Update the methods panel based on code editor content (async)
   */
  async function updateMethodsPanel() {
    const code = codeEditor.value;
    currentImports = ModuleIntrospection.detectImports(code);

    // Update module aliases map
    moduleAliases = {};
    for (const imp of currentImports) {
      if (imp.alias) {
        moduleAliases[imp.alias] = imp.module;
      }
      if (imp.type === 'from_import') {
        // Direct access methods
        moduleAliases[''] = imp.module;
      }
    }

    // If no imports, show empty state
    if (currentImports.length === 0) {
      moduleStatus.textContent = 'No module detected';
      moduleStatus.classList.remove('active', 'loading', 'error');
      methodsPanel.innerHTML = '<p class="empty-state">Import a module to see available methods</p>';
      return;
    }

    // Show loading state
    showLoading();

    try {
      // Fetch methods from backend API
      const modulesData = await ModuleIntrospection.getMethodsForImports(currentImports);

      // Hide loading
      hideLoading();

      // Update status indicator
      const moduleNames = currentImports.map(i => i.module).join(', ');
      moduleStatus.textContent = moduleNames;
      moduleStatus.classList.add('active');

      // Render methods panel
      const html = ModuleIntrospection.renderMethodsPanel(modulesData);
      methodsPanel.innerHTML = html;

      // Add click handlers to method items
      addMethodClickHandlers();

    } catch (error) {
      hideLoading();
      console.error('Failed to fetch methods:', error);
      showError(`Failed to connect to server: ${error.message}`);
    }
  }

  /**
   * Add click handlers to method items in the panel
   */
  function addMethodClickHandlers() {
    const methodItems = methodsPanel.querySelectorAll('.method-item');
    methodItems.forEach(item => {
      item.addEventListener('click', () => {
        const method = item.dataset.method;
        const params = item.dataset.params;
        insertMethodToCommand(method, params);
      });
    });
  }

  /**
   * Insert a method call into the command input
   */
  function insertMethodToCommand(method, params) {
    // If command input has content, append; otherwise replace
    if (commandInput.value.trim()) {
      commandInput.value += `; ${method}(${params})`;
    } else {
      commandInput.value = `${method}(${params})`;
    }
    commandInput.focus();

    // Select the parameters for easy editing
    const startPos = commandInput.value.lastIndexOf('(') + 1;
    const endPos = commandInput.value.lastIndexOf(')');
    if (params && startPos < endPos) {
      commandInput.setSelectionRange(startPos, endPos);
    }
  }

  /**
   * Parse and execute a command
   */
  function executeCommand(commandStr) {
    const commands = commandStr.split(';').map(c => c.trim()).filter(c => c);
    const results = [];

    for (const cmd of commands) {
      try {
        const result = parseSingleCommand(cmd);
        results.push({ command: cmd, result: result, error: false });
      } catch (err) {
        results.push({ command: cmd, result: err.message, error: true });
      }
    }

    return results;
  }

  /**
   * Parse a single command and execute it
   */
  function parseSingleCommand(cmd) {
    // Match: method(args) or alias.method(args)
    const match = cmd.match(/^(\w+)(?:\.(\w+))?\s*\((.*)\)\s*$/);

    if (!match) {
      throw new Error(`Invalid command syntax: ${cmd}`);
    }

    let methodName;
    let argsStr = match[3];

    if (match[2]) {
      // alias.method(args) format
      const alias = match[1];
      methodName = match[2];

      // Verify alias is valid
      if (!moduleAliases[alias]) {
        throw new Error(`Unknown module alias: ${alias}`);
      }
    } else {
      // method(args) format - direct call
      methodName = match[1];
    }

    // Parse arguments
    const args = parseArguments(argsStr);

    // Execute on turtle
    if (typeof turtle[methodName] === 'function') {
      return turtle[methodName](...args);
    } else {
      throw new Error(`Unknown method: ${methodName}`);
    }
  }

  /**
   * Parse argument string into array of values
   */
  function parseArguments(argsStr) {
    if (!argsStr.trim()) return [];

    const args = [];
    let current = '';
    let inString = false;
    let stringChar = '';
    let depth = 0;

    for (let i = 0; i < argsStr.length; i++) {
      const char = argsStr[i];

      if (inString) {
        current += char;
        if (char === stringChar && argsStr[i - 1] !== '\\') {
          inString = false;
        }
      } else if (char === '"' || char === "'") {
        inString = true;
        stringChar = char;
        current += char;
      } else if (char === '(' || char === '[') {
        depth++;
        current += char;
      } else if (char === ')' || char === ']') {
        depth--;
        current += char;
      } else if (char === ',' && depth === 0) {
        args.push(parseValue(current.trim()));
        current = '';
      } else {
        current += char;
      }
    }

    if (current.trim()) {
      args.push(parseValue(current.trim()));
    }

    return args;
  }

  /**
   * Parse a single value string into appropriate type
   */
  function parseValue(valStr) {
    // Number
    if (/^-?\d+\.?\d*$/.test(valStr)) {
      return parseFloat(valStr);
    }

    // String (quoted)
    if ((valStr.startsWith('"') && valStr.endsWith('"')) ||
        (valStr.startsWith("'") && valStr.endsWith("'"))) {
      return valStr.slice(1, -1);
    }

    // Boolean
    if (valStr === 'True' || valStr === 'true') return true;
    if (valStr === 'False' || valStr === 'false') return false;

    // None/null
    if (valStr === 'None' || valStr === 'null') return null;

    // Array/tuple
    if (valStr.startsWith('[') || valStr.startsWith('(')) {
      const inner = valStr.slice(1, -1);
      return parseArguments(inner);
    }

    // Return as string (color names, etc.)
    return valStr;
  }

  /**
   * Display results in output panel
   */
  function displayResults(results) {
    let html = '';

    for (const res of results) {
      html += `<div class="output-line command">&gt; ${res.command}</div>`;
      if (res.error) {
        html += `<div class="output-line error">Error: ${res.result}</div>`;
      } else if (res.result) {
        html += `<div class="output-line result">${res.result}</div>`;
      }
    }

    // Prepend to existing output
    outputDiv.innerHTML = html + outputDiv.innerHTML;

    // Remove placeholder if exists
    const placeholder = outputDiv.querySelector('.output-placeholder');
    if (placeholder) placeholder.remove();
  }

  /**
   * Run command from input
   */
  function runCommand() {
    const cmd = commandInput.value.trim();
    if (!cmd) return;

    const results = executeCommand(cmd);
    displayResults(results);

    // Clear input after successful execution
    commandInput.value = '';
  }

  // Event Listeners

  // Code editor: detect imports on change (debounced)
  let debounceTimer;
  codeEditor.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(updateMethodsPanel, 500); // Slightly longer debounce for API calls
  });

  // Run button
  runBtn.addEventListener('click', runCommand);

  // Enter key in command input
  commandInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      runCommand();
    }
  });

  // Clear canvas
  clearBtn.addEventListener('click', () => {
    turtle.clear();
    displayResults([{ command: 'clear()', result: 'Canvas cleared', error: false }]);
  });

  // Reset turtle and canvas
  resetBtn.addEventListener('click', () => {
    turtle.reset();
    displayResults([{ command: 'reset()', result: 'Turtle reset', error: false }]);
  });

  // Set default code to show the feature
  codeEditor.value = `# Type any Python import to see available methods
# The backend uses real Python introspection!

import turtle

# Try other modules too:
# import math
# import random
# import collections

# Now check the Available Methods panel!
# Click any method to insert it into Command Input
`;

  // Trigger initial update
  updateMethodsPanel();
})();
