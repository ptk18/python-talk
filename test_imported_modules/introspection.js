/**
 * Module Introspection System
 * Detects Python imports and fetches methods from backend API
 * Uses real Python introspection instead of hardcoded catalogs
 */

const ModuleIntrospection = {
  // API endpoint
  API_BASE: 'http://localhost:8001',

  // Cache for introspection results
  cache: {},

  /**
   * Detect all imported modules from code (regex-based parsing)
   * @param {string} code - Python code to analyze
   * @returns {Array} - Array of detected imports with their aliases
   */
  detectImports(code) {
    const imports = [];
    const lines = code.split('\n');

    for (const line of lines) {
      // Skip comments
      if (line.trim().startsWith('#')) continue;

      // import module
      let match = line.match(/^\s*import\s+([\w.]+)\s*$/);
      if (match) {
        const moduleName = match[1];
        imports.push({
          module: moduleName,
          alias: moduleName.split('.').pop(), // Use last part as alias for submodules
          type: 'module',
          specificImports: null
        });
        continue;
      }

      // import module as alias
      match = line.match(/^\s*import\s+([\w.]+)\s+as\s+(\w+)\s*$/);
      if (match) {
        const moduleName = match[1];
        const alias = match[2];
        imports.push({
          module: moduleName,
          alias: alias,
          type: 'module',
          specificImports: null
        });
        continue;
      }

      // from module import *
      match = line.match(/^\s*from\s+([\w.]+)\s+import\s+\*\s*$/);
      if (match) {
        const moduleName = match[1];
        imports.push({
          module: moduleName,
          alias: null, // Direct access
          type: 'from_import',
          specificImports: '*'
        });
        continue;
      }

      // from module import item1, item2
      match = line.match(/^\s*from\s+([\w.]+)\s+import\s+(.+)\s*$/);
      if (match) {
        const moduleName = match[1];
        const importList = match[2].split(',').map(s => s.trim());
        imports.push({
          module: moduleName,
          alias: null, // Direct access
          type: 'from_import',
          specificImports: importList
        });
        continue;
      }
    }

    return imports;
  },

  /**
   * Fetch methods from backend API for a module
   * @param {string} moduleName - Name of the module
   * @param {string} importType - 'module' or 'from_import'
   * @param {Array|null} names - Specific names for from_import
   * @returns {Promise<Object>} - Module methods from API
   */
  async fetchModuleMethods(moduleName, importType = 'module', names = null) {
    // Check cache first
    const cacheKey = `${moduleName}:${importType}:${names ? names.join(',') : ''}`;
    if (this.cache[cacheKey]) {
      return this.cache[cacheKey];
    }

    try {
      let url = `${this.API_BASE}/api/introspect?module=${encodeURIComponent(moduleName)}&import_type=${importType}`;

      if (names && names !== '*' && Array.isArray(names)) {
        url += `&names=${encodeURIComponent(names.join(','))}`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Cache successful results
      if (data.success) {
        this.cache[cacheKey] = data;
      }

      return data;
    } catch (error) {
      console.error(`Failed to introspect module ${moduleName}:`, error);
      return {
        success: false,
        module_name: moduleName,
        methods: [],
        error: error.message
      };
    }
  },

  /**
   * Get methods for all detected imports (async)
   * @param {Array} imports - Detected imports from detectImports()
   * @returns {Promise<Array>} - Array of module data with methods
   */
  async getMethodsForImports(imports) {
    const results = [];

    for (const importInfo of imports) {
      const names = importInfo.specificImports === '*' ? null : importInfo.specificImports;

      const data = await this.fetchModuleMethods(
        importInfo.module,
        importInfo.type,
        names
      );

      if (data.success && data.methods.length > 0) {
        results.push({
          ...data,
          alias: importInfo.alias,
          importType: importInfo.type,
          specificImports: importInfo.specificImports
        });
      } else if (!data.success) {
        // Still add failed modules to show error
        results.push({
          ...data,
          alias: importInfo.alias,
          importType: importInfo.type,
          specificImports: importInfo.specificImports
        });
      }
    }

    return results;
  },

  /**
   * Render methods panel HTML from API response
   * @param {Array} modulesData - Array of module data from getMethodsForImports()
   * @returns {string} - HTML string for methods panel
   */
  renderMethodsPanel(modulesData) {
    if (modulesData.length === 0) {
      return '<p class="empty-state">Import a module to see available methods</p>';
    }

    let html = '';

    for (const moduleData of modulesData) {
      // Show error state
      if (!moduleData.success) {
        html += `
          <div class="method-category method-category--error">
            <div class="method-category-title">${moduleData.module_name} (Error)</div>
            <p class="error-message">${moduleData.error}</p>
          </div>
        `;
        continue;
      }

      // Module header
      const methodCount = moduleData.methods.length;
      html += `
        <div class="module-header">
          <span class="module-name">${moduleData.module_name}</span>
          <span class="method-count">${methodCount} methods</span>
        </div>
      `;

      // Determine prefix for method calls
      let prefix = '';
      if (moduleData.importType === 'module' && moduleData.alias) {
        prefix = moduleData.alias + '.';
      }

      // Group methods by first letter for better organization
      const grouped = {};
      for (const method of moduleData.methods) {
        const firstLetter = method.name[0].toUpperCase();
        if (!grouped[firstLetter]) {
          grouped[firstLetter] = [];
        }
        grouped[firstLetter].push(method);
      }

      // Render methods
      html += `<div class="method-category">`;

      for (const method of moduleData.methods) {
        const params = method.required_parameters || [];
        const paramsStr = params.join(', ');
        const docstring = method.docstring
          ? method.docstring.split('\n')[0].substring(0, 100)
          : 'No description';

        html += `
          <div class="method-item"
               data-method="${prefix}${method.name}"
               data-params="${paramsStr}"
               title="${docstring}">
            ${method.name}<span class="params">(${paramsStr})</span>
          </div>
        `;
      }

      html += `</div>`;
    }

    return html;
  },

  /**
   * Clear the cache
   */
  clearCache() {
    this.cache = {};
  }
};

// Export for use in app.js
window.ModuleIntrospection = ModuleIntrospection;
