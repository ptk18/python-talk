export function parseArguments(argsStr) {
  if (!argsStr || !argsStr.trim()) return [];

  const args = [];
  let current = '';
  let inString = false;
  let stringChar = '';
  let depth = 0;

  for (let i = 0; i < argsStr.length; i++) {
    const char = argsStr[i];

    if (inString) {
      current += char;
      if (char === stringChar && argsStr[i - 1] !== '\\') inString = false;
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

  if (current.trim()) args.push(parseValue(current.trim()));
  return args;
}

export function parseValue(valStr) {
  // Handle keyword arguments (e.g., "distance=50")
  if (valStr.includes('=') && !valStr.startsWith('[') && !valStr.startsWith('(')) {
    const parts = valStr.split('=');
    if (parts.length === 2) return parseValue(parts[1].trim());
  }

  if (/^-?\d+\.?\d*$/.test(valStr)) return parseFloat(valStr);

  if ((valStr.startsWith('"') && valStr.endsWith('"')) ||
      (valStr.startsWith("'") && valStr.endsWith("'"))) {
    return valStr.slice(1, -1);
  }

  if (valStr === 'True' || valStr === 'true') return true;
  if (valStr === 'False' || valStr === 'false') return false;
  if (valStr === 'None' || valStr === 'null') return null;

  if (valStr.startsWith('[') || valStr.startsWith('(')) {
    return parseArguments(valStr.slice(1, -1));
  }

  return valStr;
}

export function parseSingleCommand(cmd, turtle) {
  const match = cmd.match(/^(\w+)(?:\.(\w+))?\s*\((.*)\)\s*$/);

  if (!match) {
    return { success: false, result: null, error: `Invalid command syntax: ${cmd}` };
  }

  const methodName = match[2] || match[1];
  const args = parseArguments(match[3]);

  if (typeof turtle[methodName] === 'function') {
    try {
      const result = turtle[methodName](...args);
      return { success: true, result, error: null };
    } catch (err) {
      return { success: false, result: null, error: err.message };
    }
  }
  return { success: false, result: null, error: `Unknown method: ${methodName}` };
}

export function executeCommands(commandStr, turtle) {
  const commands = commandStr.split(';').map(c => c.trim()).filter(c => c);
  return commands.map(cmd => ({ command: cmd, ...parseSingleCommand(cmd, turtle) }));
}

export function parseTurtleCommand(commandStr, turtle) {
  if (!commandStr || !commandStr.trim()) {
    return { success: false, result: null, error: 'Empty command' };
  }

  if (!commandStr.includes(';')) {
    return parseSingleCommand(commandStr.trim(), turtle);
  }

  const results = executeCommands(commandStr, turtle);
  const failedResults = results.filter(r => !r.success);

  if (failedResults.length > 0) {
    return {
      success: false,
      result: results.map(r => r.result).filter(r => r).join(', '),
      error: failedResults.map(r => r.error).join('; ')
    };
  }

  return {
    success: true,
    result: results.map(r => r.result).join(', '),
    error: null
  };
}

export default { parseTurtleCommand, parseSingleCommand, executeCommands, parseArguments, parseValue };
