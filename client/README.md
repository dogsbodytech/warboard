
Node v16+ required. Run `corepack enable`. (enables the package manager manager). Run `pnpm i`. (installs dependancies for this project.)

# create-svelte

Everything you need to build a Svelte project, powered by [`create-svelte`](https://github.com/sveltejs/kit/tree/master/packages/create-svelte).

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
const __dirname = __dirname || path.dirname(fileURLToPath(import.meta.url));
```


To create a production version of your app:

```bash
npmp run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://kit.svelte.dev/docs/adapters) for your target environment.
