# Gives every heading on the site the id GitHub gives it.
#
# kramdown drops the leading digits of a heading when it makes an id
# ("## 1. Repo" becomes "repo") and turns "--" into a dash first, while
# GitHub keeps both ("1-repo", "detect---json"). The documents link to
# sections in GitHub's form and tools/check_doc_links.py checks links
# against it, so before rendering this lists each page's headings from its
# Markdown source with that tool's anchors_of() and anchor() rules (-1, -2
# for repeats), and after rendering it sets those ids on the page's <h1> to
# <h6> in order, with the href and aria-labelledby of the anchor link
# just-the-docs adds.
module GitHubHeadingIds
  FENCE = /\A[ \t]*(`{3,}|~{3,})/
  ATX = /\A {0,3}(\#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*\z/
  SETEXT = /\A {0,3}(=+|-+)[ \t]*\z/
  LINK = /!?\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\([^)]*\)/
  HEADING = %r{<h([1-6])([^>]*?)\sid="([^"]*)"([^>]*)>(.*?)</h\1>}m

  # check_doc_links.py anchor(): link text only, no backticks, lower case,
  # only word characters, hyphens and spaces, spaces to hyphens.
  def self.anchor(heading)
    h = heading.gsub(LINK, '\1').delete("`").strip.downcase
    h.gsub(/[^\p{Word}\- ]/u, "").tr(" ", "-")
  end

  def self.unfenced_lines(markdown)
    fence = nil
    markdown.split("\n", -1).map do |line|
      m = FENCE.match(line)
      if fence
        fence = nil if m && m[1][0] == fence[0] && m[1].length >= fence.length &&
                       line.strip.delete(fence[0]).empty?
        ""
      elsif m
        fence = m[1]
        ""
      else
        line
      end
    end
  end

  # check_doc_links.py anchors_of(), in document order.
  def self.ids_of(markdown)
    lines = unfenced_lines(markdown)
    seen = Hash.new(0)
    ids = []
    lines.each_with_index do |line, i|
      heading = nil
      if (m = ATX.match(line))
        heading = m[2]
      elsif i.positive? && SETEXT.match?(line) && !lines[i - 1].strip.empty? &&
            !ATX.match?(lines[i - 1]) &&
            !(line.strip.start_with?("-") && lines[i - 1].lstrip.start_with?("-", "*", "|"))
        heading = lines[i - 1]
      end
      next if heading.nil?

      a = anchor(heading)
      n = seen[a]
      seen[a] += 1
      ids << (n.zero? ? a : "#{a}-#{n}")
    end
    ids
  end

  def self.rewrite(html, ids)
    i = -1
    html.gsub(HEADING) do
      level, before, old_id, after, inner = $1, $2, $3, $4, $5
      i += 1
      id = ids[i]
      inner = inner.sub(%(href="##{old_id}"), %(href="##{id}"))
                   .sub(%(aria-labelledby="#{old_id}"), %(aria-labelledby="#{id}"))
      %(<h#{level}#{before} id="#{id}"#{after}>#{inner}</h#{level}>)
    end
  end
end

Jekyll::Hooks.register [:pages, :documents], :pre_render, priority: :high do |doc|
  next unless doc.extname.casecmp(".md").zero?

  doc.data["github_heading_ids"] = GitHubHeadingIds.ids_of(doc.content)
end

Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  ids = doc.data["github_heading_ids"]
  next if ids.nil?

  # Only the page content holds document headings; the layout's own
  # markup (navigation, search) is left alone.
  doc.output = doc.output.sub(%r{(<main[^>]*>)(.*)(</main>)}m) do
    open_tag, body, close_tag = $1, $2, $3
    found = body.scan(GitHubHeadingIds::HEADING).length
    if found == ids.length
      body = GitHubHeadingIds.rewrite(body, ids)
    else
      Jekyll.logger.warn "Heading ids:",
                         "#{doc.relative_path} has #{ids.length} headings in its " \
                         "source and #{found} in its HTML; kramdown ids kept"
    end
    "#{open_tag}#{body}#{close_tag}"
  end
end
