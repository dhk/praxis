/* Minimal Markdown renderer for report.md: headings, paragraphs, tables,
   fenced code, inline code/bold/italic/links. Escapes all input first. */

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;');
}

function inline(s) {
  let out = escapeHtml(s);
  out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  out = out.replace(/(^|[^*])\*([^*]+)\*/g, '$1<em>$2</em>');
  out = out.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g,
    '<a href="$2" rel="noopener">$1</a>');
  return out;
}

function isTableRow(line) {
  return /^\s*\|.*\|\s*$/.test(line);
}

function isTableSeparator(line) {
  return /^\s*\|(\s*:?-+:?\s*\|)+\s*$/.test(line);
}

function cells(line) {
  // Split on '|' that isn't backslash-escaped (report.py escapes literal '|'
  // in cell content as '\|' so it can't be mistaken for a column delimiter),
  // then unescape '\|' and '\\' within each cell.
  const trimmed = line.trim().replace(/^\||\|$/g, '');
  return trimmed.split(/(?<!\\)\|/).map((c) => c.trim().replace(/\\\|/g, '|').replace(/\\\\/g, '\\'));
}

export function renderMarkdown(md) {
  const lines = md.split('\n');
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    if (/^```/.test(line)) {
      const buf = [];
      i += 1;
      while (i < lines.length && !/^```/.test(lines[i])) { buf.push(lines[i]); i += 1; }
      i += 1;
      out.push(`<pre>${escapeHtml(buf.join('\n'))}</pre>`);
      continue;
    }

    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      const level = Math.min(h[1].length, 3);
      out.push(`<h${level}>${inline(h[2])}</h${level}>`);
      i += 1;
      continue;
    }

    if (isTableRow(line) && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const head = cells(line);
      i += 2;
      const rows = [];
      while (i < lines.length && isTableRow(lines[i])) { rows.push(cells(lines[i])); i += 1; }
      const thead = head.map((c) => `<th>${inline(c)}</th>`).join('');
      const tbody = rows.map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join('')}</tr>`).join('');
      out.push(`<div class="table-wrap"><table class="data"><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table></div>`);
      continue;
    }

    if (line.trim() === '') { i += 1; continue; }

    const buf = [line];
    i += 1;
    while (i < lines.length && lines[i].trim() !== '' && !/^(#{1,6}\s|```)/.test(lines[i]) && !isTableRow(lines[i])) {
      buf.push(lines[i]);
      i += 1;
    }
    out.push(`<p>${inline(buf.join(' '))}</p>`);
  }
  return out.join('\n');
}

export { escapeHtml };
