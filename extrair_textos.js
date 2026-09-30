// Extrai do apresentacao-tds.html todas as frases que os robôs falam.
// Usado por gerar_audios.py (não precisa rodar manualmente).
// Saída: [[id, texto, quem], ...]   quem = "m" (masculino) ou "f" (feminino)
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const html = fs.readFileSync(path.join(__dirname, "apresentacao-tds.html"), "utf8");
const blocos = [...html.matchAll(/\/\*T:INI\*\/([\s\S]*?)\/\*T:FIM\*\//g)].map(m => m[1]);
if (!blocos.length) { console.error("Marcadores /*T:INI*/ não encontrados no HTML."); process.exit(1); }

const codigo = blocos.join("\n") + `
;JSON.stringify([...new Map(
  allTexts().flatMap(([w, t]) => splitParts(t).map(s => [w, s]))
            .map(([w, s]) => [clipId(w, s), [clipId(w, s), clean(s), w]])
).values()]);`;

const resultado = vm.runInNewContext(codigo, {});
process.stdout.write(resultado);
