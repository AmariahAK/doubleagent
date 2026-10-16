# Points links to files that are not site pages at the file on GitHub.
#
# The documents link to the license, to directories and to files the site
# excludes (CLAUDE.md, the scripts) with paths relative to the citing file,
# which work on GitHub. jekyll-relative-links turns every link to a page
# into its URL; a relative link left after that has no page behind it, so
# this rewrites it to the same path under source_url in _config.yml
# (tree/ for a directory, blob/ for a file), keeping any #fragment.
module GitHubSourceLinks
  HREF = /(<a\s[^>]*?href=")([^"#:]+)((?:#[^"]*)?")/

  def self.rewrite(html, source_dir, site)
    base = site.config["source_url"]
    html.gsub(HREF) do
      open_attr, path, rest = $1, $2, $3
      next "#{open_attr}#{path}#{rest}" if path.start_with?("/")

      rel = File.expand_path(path, "/#{source_dir}").delete_prefix("/")
      kind = File.directory?(File.join(site.source, rel)) ? "tree" : "blob"
      "#{open_attr}#{base}/#{kind}/main/#{rel}#{rest}"
    end
  end
end

Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  next unless doc.extname.casecmp(".md").zero?

  source_dir = File.dirname(doc.relative_path).sub(/\A\.\z/, "")
  doc.output = doc.output.sub(%r{(<main[^>]*>)(.*)(</main>)}m) do
    "#{$1}#{GitHubSourceLinks.rewrite($2, source_dir, doc.site)}#{$3}"
  end
end
