
Node v16+ required. Run `corepack enable`. (enables the package manager manager). Run `pnpm i`. (installs dependancies for this project.)

# create-svelte

If deploying, go here: [DEPLOY.md](DEPLOY.md)

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npmp run dev

# or start the server and open the app in a new browser tab
npmp run dev -- --open
```

## Building
ensure `node_modules/@sveltejs/adapter-node/files/handler-393b2283.js` line 1055 is

```js
let __dirname;
try {
  __dirname = path.dirname(fileURLToPath(import.meta.url))
} catch (e) {
  try {
    __dirname = path.dirname(resolve(".", process.argv[1] ))
  } catch (e) { }
}
```

To create a production version of your app:

```bash
pnpm run build
```

ensure bundlebuild/client is empty, then:

```bash
pnpm exec esbuild build/index.js --bundle --minify --platform=node --target=node18 --outdir=bundledbuild --external:build/client/*
cp -r build/client bundledbuild/client
```

then copy to server:

```bash
# if running silently prefix with
# sshpass -p "pass"
scp -r ./bundledbuild/* root@joeltest.dogshost.com:/root/deploy/
```

on the server run:

```bash
# enuse you explicitly reference index.js, rather than just the directory
# because the code that picks up the directory it's in relies on argv.
node deploy/index.js
```

