#!/usr/bin/env node
const Database = require('better-sqlite3')
const path = require('path')
const fs = require('fs')

const DATA_DIR = path.join(__dirname, 'data')
const DB_FILES = {
  jmejcat: path.join(DATA_DIR, 'jmejcat.db'),
  tramitacio: path.join(DATA_DIR, 'tramitacio.db'),
}

function openDB(name, readonly = true) {
  const dbPath = DB_FILES[name]
  if (!fs.existsSync(dbPath)) {
    console.error(`ERROR: ${name} not found at ${dbPath}`)
    process.exit(1)
  }
  const db = new Database(dbPath, { readonly })
  db.pragma('busy_timeout = 5000')
  if (!readonly) {
    db.pragma('journal_mode = WAL')
  }
  return db
}

function listTramits(opts) {
  const db = openDB('tramitacio')
  let sql = 'SELECT * FROM tramitacio WHERE 1=1'
  const params = []
  if (opts.numero) { sql += ' AND numero LIKE ?'; params.push(`%${opts.numero}%`) }
  if (opts.any) { sql += ' AND any = ?'; params.push(opts.any) }
  if (opts.color) { sql += ' AND color = ?'; params.push(opts.color) }
  if (opts.id) { sql += ' AND id = ?'; params.push(opts.id) }
  sql += ' ORDER BY updated_at DESC'
  if (opts.limit) { sql += ' LIMIT ?'; params.push(opts.limit) }
  const rows = db.prepare(sql).all(...params)
  db.close()
  return rows
}

function listNotes(opts) {
  const db = openDB('jmejcat')
  let sql = 'SELECT * FROM notes WHERE 1=1'
  const params = []
  if (opts.title) { sql += ' AND title LIKE ?'; params.push(`%${opts.title}%`) }
  if (opts.id) { sql += ' AND id = ?'; params.push(opts.id) }
  sql += ' ORDER BY updated_at DESC'
  if (opts.limit) { sql += ' LIMIT ?'; params.push(opts.limit) }
  const rows = db.prepare(sql).all(...params)
  db.close()
  return rows
}

function listImages(noteId) {
  const db = openDB('jmejcat')
  const rows = db.prepare('SELECT * FROM images WHERE note_id = ? ORDER BY sort_order').all(noteId)
  db.close()
  return rows
}

function stats() {
  const dbj = openDB('jmejcat')
  const dbt = openDB('tramitacio')
  const result = {
    notes: dbj.prepare('SELECT COUNT(*) as count FROM notes').get().count,
    images: dbj.prepare('SELECT COUNT(*) as count FROM images').get().count,
    tramits: dbt.prepare('SELECT COUNT(*) as count FROM tramitacio').get().count,
  }
  dbj.close(); dbt.close()
  return result
}

function insertTramit(data) {
  const db = openDB('tramitacio', false)
  const stmt = db.prepare('INSERT INTO tramitacio (numero, any, data, info, color) VALUES (?, ?, ?, ?, ?)')
  const now = new Date().toISOString().replace('T', ' ').slice(0, 19)
  const result = stmt.run(data.numero || '', data.any || new Date().getFullYear(), data.data || '', data.info || '', data.color || '')
  db.close()
  return { id: result.lastInsertRowid, changes: result.changes }
}

function updateTramit(id, data) {
  const db = openDB('tramitacio', false)
  const fields = []; const values = []
  for (const k of ['numero', 'any', 'data', 'info', 'color']) {
    if (data[k] !== undefined) { fields.push(`${k} = ?`); values.push(data[k]) }
  }
  if (fields.length === 0) { db.close(); return { error: 'no fields to update' } }
  const now = new Date().toISOString().replace('T', ' ').slice(0, 19)
  fields.push('updated_at = ?'); values.push(now)
  values.push(id)
  const result = db.prepare(`UPDATE tramitacio SET ${fields.join(', ')} WHERE id = ?`).run(...values)
  db.close()
  return { changes: result.changes }
}

function deleteTramit(id) {
  const db = openDB('tramitacio', false)
  const result = db.prepare('DELETE FROM tramitacio WHERE id = ?').run(id)
  db.close()
  return { changes: result.changes }
}

function insertNote(data) {
  const db = openDB('jmejcat', false)
  const stmt = db.prepare('INSERT INTO notes (title, request, solution, examples) VALUES (?, ?, ?, ?)')
  const result = stmt.run(data.title || '', data.request || '', data.solution || '', data.examples || '')
  db.close()
  return { id: result.lastInsertRowid, changes: result.changes }
}

function updateNote(id, data) {
  const db = openDB('jmejcat', false)
  const fields = []; const values = []
  for (const k of ['title', 'request', 'solution', 'examples']) {
    if (data[k] !== undefined) { fields.push(`${k} = ?`); values.push(data[k]) }
  }
  if (fields.length === 0) { db.close(); return { error: 'no fields to update' } }
  const now = new Date().toISOString().replace('T', ' ').slice(0, 19)
  fields.push('updated_at = ?'); values.push(now)
  values.push(id)
  const result = db.prepare(`UPDATE notes SET ${fields.join(', ')} WHERE id = ?`).run(...values)
  db.close()
  return { changes: result.changes }
}

function deleteNote(id) {
  const db = openDB('jmejcat', false)
  const result = db.prepare('DELETE FROM notes WHERE id = ?').run(id)
  db.close()
  return { changes: result.changes }
}

function checkpoint(name) {
  const dbPath = DB_FILES[name]
  if (!fs.existsSync(dbPath)) { console.error(`ERROR: ${name} not found`); process.exit(1) }
  const db = new Database(dbPath)
  const result = db.pragma('wal_checkpoint(TRUNCATE)')
  db.close()
  return result
}

const args = process.argv.slice(2)
const mode = args[0] || 'help'

switch (mode) {
  case 'tramits':
  case 't': {
    const isIdSearch = args[1] && !isNaN(parseInt(args[1])) && args.length === 2
    const opts = {
      numero: isIdSearch ? '' : (args[1] || ''),
      any: parseInt(args[2]) || null,
      color: args[3] || '',
      limit: parseInt(args[4]) || 50,
      id: isIdSearch ? parseInt(args[1]) : null,
    }
    console.log(JSON.stringify(listTramits(opts), null, 2))
    break
  }
  case 'notes':
  case 'n': {
    const isIdSearch = args[1] && !isNaN(parseInt(args[1])) && args.length === 2
    const opts = { title: isIdSearch ? '' : (args[1] || ''), limit: parseInt(args[2]) || 50, id: isIdSearch ? parseInt(args[1]) : null }
    console.log(JSON.stringify(listNotes(opts), null, 2))
    break
  }
  case 'images':
  case 'i': {
    const noteId = parseInt(args[1])
    if (!noteId) { console.error('Usage: query.js images <note_id>'); process.exit(1) }
    console.log(JSON.stringify(listImages(noteId), null, 2))
    break
  }
  case 'stats':
  case 's':
    console.log(JSON.stringify(stats(), null, 2))
    break
  case 'checkpoint':
  case 'c': {
    const name = args[1] || 'all'
    if (name === 'all') {
      console.log('jmejcat:', checkpoint('jmejcat'))
      console.log('tramitacio:', checkpoint('tramitacio'))
    } else {
      console.log(name + ':', checkpoint(name))
    }
    break
  }
  case 'ti':
  case 'tramit-insert': {
    if (args.length < 4) { console.error('Usage: query.js ti <numero> <any> <data> <info> [color]'); process.exit(1) }
    console.log(JSON.stringify(insertTramit({ numero: args[1], any: parseInt(args[2]), data: args[3], info: args[4], color: args[5] || '' }), null, 2))
    break
  }
  case 'tu':
  case 'tramit-update': {
    const id = parseInt(args[1])
    if (!id) { console.error('Usage: query.js tu <id> [--numero x] [--any x] [--data x] [--info x] [--color x]'); process.exit(1) }
    const data = {}
    for (let i = 2; i < args.length; i += 2) {
      const key = args[i].replace('--', '')
      if (key === 'any') data[key] = parseInt(args[i + 1])
      else data[key] = args[i + 1]
    }
    console.log(JSON.stringify(updateTramit(id, data), null, 2))
    break
  }
  case 'td':
  case 'tramit-delete': {
    const id = parseInt(args[1])
    if (!id) { console.error('Usage: query.js td <id>'); process.exit(1) }
    console.log(JSON.stringify(deleteTramit(id), null, 2))
    break
  }
  case 'ni':
  case 'note-insert': {
    if (args.length < 3) { console.error('Usage: query.js ni <title> <request> [solution] [examples]'); process.exit(1) }
    console.log(JSON.stringify(insertNote({ title: args[1], request: args[2], solution: args[3] || '', examples: args[4] || '' }), null, 2))
    break
  }
  case 'nu':
  case 'note-update': {
    const nid = parseInt(args[1])
    if (!nid) { console.error('Usage: query.js nu <id> [--title x] [--request x] [--solution x] [--examples x]'); process.exit(1) }
    const ndata = {}
    for (let i = 2; i < args.length; i += 2) {
      ndata[args[i].replace('--', '')] = args[i + 1]
    }
    console.log(JSON.stringify(updateNote(nid, ndata), null, 2))
    break
  }
  case 'nd':
  case 'note-delete': {
    const ndid = parseInt(args[1])
    if (!ndid) { console.error('Usage: query.js nd <id>'); process.exit(1) }
    console.log(JSON.stringify(deleteNote(ndid), null, 2))
    break
  }
  default:
    console.log(`
JMEJCat Query Tool (better-sqlite3)
Usage: node query.js <command> [args]

Read commands:
  t|tramits     [search] [any] [color] [limit]   List tramitacions
  n|notes       [search] [limit]                 List notes
  i|images      <note_id>                        Get images for a note
  s|stats                                         Show DB statistics

Write commands:
  ti|tramit-insert <numero> <any> <data> <info> [color]    Insert tramit
  tu|tramit-update <id> --field val [...fields]             Update tramit
  td|tramit-delete <id>                                     Delete tramit
  ni|note-insert <title> <request> [solution] [examples]    Insert note
  nu|note-update <id> --field val [...fields]               Update note
  nd|note-delete <id>                                       Delete note

Utils:
  c|checkpoint  [jmejcat|tramitacio|all]                   Force WAL checkpoint

Examples:
  node query.js t "exp"                    Search tramits
  node query.js ti "9999" 2026 "01/07/2026" "prova" "blau"
  node query.js tu 100 --info "nou text" --color "verd"
  node query.js td 999
  node query.js ni "Titol prova" "<p>request</p>" "<p>solution</p>"
  node query.js nu 5 --title "Nou titol"
  node query.js nd 999
  node query.js s                          Statistics
  node query.js c all                      Checkpoint both DBs
`)
}