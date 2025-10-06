# Hello Rust

## First time setup

## Resources

- https://dystroy.org/bacon/
- https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer
- https://www.sea-ql.org/SeaORM/docs/generate-entity/sea-orm-cli/

### Orm

```sh
sea-orm-cli migrate down; sea-orm-cli migrate up
```

### VSCode settings

```json
"[rust]": {
  "editor.defaultFormatter": "rust-lang.rust-analyzer"
},

"rust-analyzer.check.command": "clippy"
```
