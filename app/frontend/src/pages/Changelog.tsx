import { useEffect, useState } from 'react'
import Markdown from 'react-markdown'

export default function Changelog() {
  const [changelog, setChangelog] = useState('')

  useEffect(() => {
    fetch('/CHANGELOG.md')
      .then((res) => res.text())
      .then((text) => {
        // Remove the "# Changelog" header since we use section-title
        const withoutHeader = text.replace(/^#\s+Changelog\s*\n+/, '')
        setChangelog(withoutHeader)
      })
      .catch(() => setChangelog('## Error\n\n- Failed to load changelog.'))
  }, [])

  return (
    <section className="changelog">
      <div className="container">
        <div className="section-title">
          <h2>Changelog</h2>
          <p>Version history and updates</p>
        </div>

        <div className="changelog-content">
          <Markdown>{changelog}</Markdown>
        </div>
      </div>
    </section>
  )
}
