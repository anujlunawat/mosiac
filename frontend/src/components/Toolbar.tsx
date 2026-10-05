import type { Editor } from '@tiptap/react'
import {
  Bold, Italic, Underline, Strikethrough, Code,
  Heading1, Heading2, Heading3,
  List, ListOrdered, ListTodo,
  Quote, FileCode,
  AlignLeft, AlignCenter, AlignRight,
  Highlighter, Link as LinkIcon,
  Undo2, Redo2,
  Minus,
} from 'lucide-react'

interface Props {
  editor: Editor | null
}

interface ToolbarBtnProps {
  onClick: () => void
  active?: boolean
  disabled?: boolean
  title: string
  children: React.ReactNode
  id: string
}

function Btn({ onClick, active, disabled, title, children, id }: ToolbarBtnProps) {
  return (
    <button
      id={id}
      onClick={onClick}
      disabled={disabled}
      title={title}
      aria-label={title}
      aria-pressed={active}
      className={`toolbar-btn ${active ? 'active' : ''}`}
      type="button"
    >
      {children}
    </button>
  )
}

function Sep() {
  return <div className="toolbar-sep" aria-hidden="true" />
}

const ICON_SIZE = 15

export function Toolbar({ editor }: Props) {
  if (!editor) return null

  const setLink = () => {
    const prev = editor.getAttributes('link').href as string | undefined
    const url = window.prompt('Enter URL:', prev || 'https://')
    if (url === null) return // cancelled
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }
    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }

  return (
    <div className="toolbar" role="toolbar" aria-label="Text formatting">
      {/* History */}
      <div className="toolbar-group">
        <Btn id="btn-undo" onClick={() => editor.chain().focus().undo().run()} disabled={!editor.can().undo()} title="Undo (Ctrl+Z)">
          <Undo2 size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-redo" onClick={() => editor.chain().focus().redo().run()} disabled={!editor.can().redo()} title="Redo (Ctrl+Y)">
          <Redo2 size={ICON_SIZE} />
        </Btn>
      </div>

      <Sep />

      {/* Inline formatting */}
      <div className="toolbar-group">
        <Btn id="btn-bold" onClick={() => editor.chain().focus().toggleBold().run()} active={editor.isActive('bold')} title="Bold (Ctrl+B)">
          <Bold size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-italic" onClick={() => editor.chain().focus().toggleItalic().run()} active={editor.isActive('italic')} title="Italic (Ctrl+I)">
          <Italic size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-underline" onClick={() => editor.chain().focus().toggleUnderline().run()} active={editor.isActive('underline')} title="Underline (Ctrl+U)">
          <Underline size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-strike" onClick={() => editor.chain().focus().toggleStrike().run()} active={editor.isActive('strike')} title="Strikethrough">
          <Strikethrough size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-code" onClick={() => editor.chain().focus().toggleCode().run()} active={editor.isActive('code')} title="Inline Code">
          <Code size={ICON_SIZE} />
        </Btn>
      </div>

      <Sep />

      {/* Headings */}
      <div className="toolbar-group">
        <Btn id="btn-h1" onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} active={editor.isActive('heading', { level: 1 })} title="Heading 1">
          <Heading1 size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-h2" onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} active={editor.isActive('heading', { level: 2 })} title="Heading 2">
          <Heading2 size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-h3" onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} active={editor.isActive('heading', { level: 3 })} title="Heading 3">
          <Heading3 size={ICON_SIZE} />
        </Btn>
      </div>

      <Sep />

      {/* Lists */}
      <div className="toolbar-group">
        <Btn id="btn-bullet" onClick={() => editor.chain().focus().toggleBulletList().run()} active={editor.isActive('bulletList')} title="Bullet List">
          <List size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-ordered" onClick={() => editor.chain().focus().toggleOrderedList().run()} active={editor.isActive('orderedList')} title="Numbered List">
          <ListOrdered size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-task" onClick={() => editor.chain().focus().toggleTaskList().run()} active={editor.isActive('taskList')} title="Task List">
          <ListTodo size={ICON_SIZE} />
        </Btn>
      </div>

      <Sep />

      {/* Blocks */}
      <div className="toolbar-group">
        <Btn id="btn-quote" onClick={() => editor.chain().focus().toggleBlockquote().run()} active={editor.isActive('blockquote')} title="Blockquote">
          <Quote size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-codeblock" onClick={() => editor.chain().focus().toggleCodeBlock().run()} active={editor.isActive('codeBlock')} title="Code Block">
          <FileCode size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-hr" onClick={() => editor.chain().focus().setHorizontalRule().run()} title="Horizontal Rule">
          <Minus size={ICON_SIZE} />
        </Btn>
      </div>

      <Sep />

      {/* Text alignment */}
      <div className="toolbar-group">
        <Btn id="btn-align-left" onClick={() => editor.chain().focus().setTextAlign('left').run()} active={editor.isActive({ textAlign: 'left' })} title="Align Left">
          <AlignLeft size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-align-center" onClick={() => editor.chain().focus().setTextAlign('center').run()} active={editor.isActive({ textAlign: 'center' })} title="Align Center">
          <AlignCenter size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-align-right" onClick={() => editor.chain().focus().setTextAlign('right').run()} active={editor.isActive({ textAlign: 'right' })} title="Align Right">
          <AlignRight size={ICON_SIZE} />
        </Btn>
      </div>

      <Sep />

      {/* Extras */}
      <div className="toolbar-group">
        <Btn id="btn-highlight" onClick={() => editor.chain().focus().toggleHighlight().run()} active={editor.isActive('highlight')} title="Highlight">
          <Highlighter size={ICON_SIZE} />
        </Btn>
        <Btn id="btn-link" onClick={setLink} active={editor.isActive('link')} title="Insert Link">
          <LinkIcon size={ICON_SIZE} />
        </Btn>
      </div>
    </div>
  )
}
