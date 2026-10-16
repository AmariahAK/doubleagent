# Renders code spans as GitHub does where kramdown differs.
#
# Several documents quote exact prefixes in code spans that begin with a
# space (` requested=<id>`); the space is the point, which is why
# markdownlint's MD038 is off. kramdown reads a backtick followed by a
# space as a literal backtick, and it ends a paragraph at a line that
# starts with a tag, even inside a code span wrapped across lines
# (`model:` then `<old> -> <new>`), so the span's <...> becomes raw HTML
# and the rest of the page is swallowed. Before conversion this joins the
# lines of every code span with spaces (CommonMark renders a line break in
# a span as a space) and writes each single-backtick span that starts with
# a space as an HTML <code> element with its content escaped, which keeps
# the space in paragraphs and table cells. Fenced code blocks are left alone.
module GitHubCodeSpans
  FENCE = /\A[ \t]*(`{3,}|~{3,})/

  # kramdown passes a <code> element's content through as it is, in a
  # paragraph and in a table cell alike.
  def self.html_code(body)
    escaped = body.gsub("&", "&amp;").gsub("<", "&lt;").gsub(">", "&gt;")
    %(<code class="language-plaintext highlighter-rouge">#{escaped}</code>)
  end

  # Pairs backtick runs left to right as CommonMark does: a run opens a
  # span that the next run of the same length closes, within a paragraph.
  def self.rewrite_text(text)
    out = +""
    pos = 0
    while (open = text.index(/`+/, pos))
      run = text[open..][/\A`+/]
      out << text[pos...open]
      stop = text.index("\n\n", open) || text.length
      close = nil
      search = open + run.length
      while (m = text.match(/`+/, search)) && m.begin(0) < stop
        if m[0].length == run.length
          close = m.begin(0)
          break
        end
        search = m.end(0)
      end
      if close.nil?
        out << run
        pos = open + run.length
        next
      end
      body = text[(open + run.length)...close].tr("\n", " ")
      out << if run.length == 1 && body.start_with?(" ") && !body.strip.empty?
               html_code(body)
             else
               "#{run}#{body}#{run}"
             end
      pos = close + run.length
    end
    out << text[pos..]
  end

  def self.rewrite(markdown)
    out = []
    chunk = []
    fence = nil
    markdown.each_line do |line|
      m = FENCE.match(line)
      if fence
        out << line
        fence = nil if m && m[1][0] == fence[0] && m[1].length >= fence.length &&
                       line.strip.delete(fence[0]).empty?
      elsif m
        out << rewrite_text(chunk.join)
        chunk = []
        fence = m[1]
        out << line
      else
        chunk << line
      end
    end
    out << rewrite_text(chunk.join)
    out.join
  end
end

Jekyll::Hooks.register [:pages, :documents], :pre_render do |doc|
  next unless doc.extname.casecmp(".md").zero?

  doc.content = GitHubCodeSpans.rewrite(doc.content)
end
