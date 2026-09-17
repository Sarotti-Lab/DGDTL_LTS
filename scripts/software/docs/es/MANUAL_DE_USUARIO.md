# DGDTL-LTS / U-MaxP — Manual de Usuario

Este manual describe los flujos distribuidos en la versión 1.0.0. Para una
primera ejecución, utilice Unified con la guía de despliegue de un ejemplo.
Hunter realiza la búsqueda completa y puede requerir considerablemente más
tiempo y recursos de cómputo. Los investigadores también pueden utilizar sus
propios conjuntos de datos.

Hunter está diseñado para ejecutar la búsqueda completa en clústeres de
cómputo. También admite ejecuciones locales en Linux y en Windows mediante los
lanzadores Docker/WSL2 distribuidos, siempre que se disponga de recursos de
cómputo adecuados para el dominio seleccionado.

[English user guide](../en/USER_GUIDE.md).

## Seleccione la vía de ejecución

| Plataforma | Vía | Preparación inicial |
| --- | --- | --- |
| Linux nativo | Python dentro del entorno congelado `dgdtl_v2` | Preparar el entorno e instalar ambos wheels distribuidos. |
| Windows x86-64 | Lanzadores `.cmd` mediante Docker Desktop/WSL2 con contenedores Linux | Preparar Docker Desktop y utilizar el Certified Runtime distribuido. No se necesita instalar Python científico en Windows. |

La distribución ofrece todos los componentes juntos. Cada flujo utiliza sólo
algunos de ellos. Mantenga la instalación del software separada de la carpeta
de trabajo de cada ejecución, que contiene los datos seleccionados y recibe
los nuevos resultados.

## Preparación certificada

### Linux: preparar una vez y activar en cada sesión

Ejecute los comandos de instalación desde la carpeta `software`. Mamba debe
estar disponible previamente. Si todavía no creó el entorno de referencia:

```bash
mamba env create -f environment/dgdtl_v2.yml
```

Active el entorno:

```bash
mamba activate dgdtl_v2
python --version
```

El intérprete de referencia es Python 3.12.12. Antes de instalar los wheels,
realice la [comprobación de versiones científicas registradas](../../environment/README.md#linux-check-the-recorded-scientific-package-versions).
El YAML conservado no fija explícitamente todas las versiones científicas
registradas: `joblib` y `statsmodels` requieren particular atención. El nombre
del entorno o su creación exitosa no demuestran por sí solos que la instalación
coincida. Resuelva las dependencias ausentes o diferentes antes de una
ejecución de referencia.

Instale los wheels locales dentro de ese entorno preparado:

```bash
python -m pip install --no-index --no-deps \
  dist/dgdtl_lts-1.0.0-py3-none-any.whl \
  dist/u_maxp-1.0.0-py3-none-any.whl
python -m pip check
```

La creación del entorno puede requerir acceso a los canales configurados por
red; esta instalación de wheels utiliza archivos locales y no instala
dependencias. Si el entorno y los wheels exactos ya están instalados, actívelos
y compruébelos sin repetir la instalación. Confirme versiones y ubicaciones:

```bash
python -c "import importlib.metadata as m, dgdtl_lts, u_maxp; print(m.version('dgdtl-lts'), dgdtl_lts.__file__); print(m.version('u-maxp'), u_maxp.__file__)"
```

Ambas distribuciones tienen la versión 1.0.0. Los imports deben resolverse desde
`site-packages` del entorno activo. Consulte la [documentación del entorno](../../environment/README.md)
para la preparación completa y sus límites de reproducibilidad. La coincidencia
de versiones por sí sola no establece identidad binaria ni amplía el alcance
certificado.

### Windows: utilizar el runtime instalado

Utilice Windows x86-64, PowerShell 5.1 y Docker Desktop con WSL2 y contenedores
Linux. Inicie Docker Desktop antes de ejecutar un flujo. Python y ambos
paquetes científicos ya están instalados dentro del runtime Linux distribuido;
en Windows no se crea un entorno del sistema anfitrión a partir del YAML ni se
instalan los wheels en un Python de Windows.

Los lanzadores existentes preparan las fuentes Arial controladas a partir del
paquete offline incluido cuando es necesario. En la primera preparación, lea
la licencia de Microsoft incluida e introduzca `I ACCEPT` si acepta sus
condiciones. No necesita descargar las fuentes por separado ni copiarlas de
una carpeta de certificación. Consulte las
[instrucciones del lanzador de Windows](../../launchers/windows/README.md).

## Archivos necesarios para ejecutar

| Uso | Componentes de ejecución, además del entorno preparado | Datos científicos de entrada |
| --- | --- | --- |
| Linux, script Python propio | El script y los módulos adicionales que utilice. | Los datos requeridos por ese script. |
| Linux, Hunter | `orchestrators/dgdtl_hunter_umaxp_cluster.py`; conserve `dgdtl_reporting.py` junto a él para la presentación de consola distribuida. | CSV de entrenamiento y validación y opciones de modelado. |
| Linux, Unified con informes y figuras completos | `orchestrators/dgdtl_unified_umaxp.py`, `plotting_style.py` y `reporting.py`, conservados juntos. | CSV de entrenamiento, validación y test; una guía en el modo Deployment Guide. |
| Windows, Hunter o Unified | `.cmd` seleccionado, orquestador Python y módulos acompañantes, transporte de Windows, runtime y recursos de fuentes controladas. Hunter también utiliza `launchers/linux/create_local_sh_dgdtl_lts.py` para configurarse. | Los mismos CSV y configuración o guía correspondientes al flujo seleccionado. |

Hunter dispone de una alternativa de consola si `dgdtl_reporting.py` no está
disponible. Unified desactiva una parte de la generación de informes y figuras
si no puede importar alguno de sus dos módulos acompañantes; conserve ambos
para obtener el conjunto completo de salidas de referencia. La ejecución
directa en Linux no necesita el transporte de Windows ni el archivo OCI del
runtime; los generadores de lanzadores Linux son ayudas opcionales.

Windows utiliza los componentes de ejecución indicados, pero su lanzador
también verifica cada archivo de `manifests/RELEASE_CONTENTS.sha256`. Conserve
ese manifiesto y todos los archivos que enumera en la distribución, incluidos
los documentos y resultados de referencia. Este requisito adicional de
integridad no convierte esos archivos en datos científicos de entrada. La tabla
no indica qué extraer para crear una instalación reducida de Windows. Los
[requisitos de archivos de la release](../../README.md#files-needed-for-each-use)
detallan las rutas; la [descripción de los lanzadores](../../launchers/README.md)
explica las formas de uso admitidas.

## Datos de entrada

Hunter requiere CSV de entrenamiento y validación interna. Unified también
lee un CSV de test. Cada partición debe conservar los mismos nombres y orden
de columnas: identificador primero, predictores en las columnas intermedias
y respuesta numérica al final. Las fórmulas de características utilizan los
nombres de los predictores. Mantenga las particiones y la configuración
coherentes entre Hunter y Unified al evaluar una configuración seleccionada
por Hunter.

Para sus propios datos, seleccione el modo de modelado, las restricciones, las
fórmulas de características y las transformaciones apropiadas para el estudio.
No necesita ningún conjunto de datos de ejemplo ni resultado de referencia
como entrada. El modo interactivo de Unified puede utilizarse sin una guía de
despliegue. En el modo Deployment Guide, proporcione una guía correspondiente
a su configuración y los nombres predeterminados de CSV descritos más abajo.

## Prepare una carpeta de trabajo

Seleccione una carpeta nueva fuera de `software` para cada ejecución. No
utilice una carpeta de resultados de referencia como destino de nuevas salidas.
Mantenga los scripts instalados en la distribución cuando los invoque por su
ruta, como se muestra a continuación.

Para un primer ejemplo, estos comandos copian únicamente los CSV y la guía de
D01. Reemplace la ruta del software y elija un nombre de carpeta de trabajo
que todavía no haya utilizado.

### Ejemplo en Linux

Con el entorno preparado y activo:

```bash
DGDTL_SOFTWARE="/absolute/path/to/software"
DGDTL_WORKDIR="$HOME/dgdtl_runs/d01_01"
mkdir -p "$DGDTL_WORKDIR"
cp "$DGDTL_SOFTWARE/examples/d01/"data_*.csv \
   "$DGDTL_SOFTWARE/examples/d01/"DGDTL_Report_*.txt \
   "$DGDTL_WORKDIR/"
cd "$DGDTL_WORKDIR"
```

### Ejemplo en Windows

En PowerShell 5.1:

```powershell
$DGDTLSoftware = 'C:\DGDTL\software'
$DGDTLWorkdir = Join-Path $env:USERPROFILE 'dgdtl_runs\d01_01'
New-Item -ItemType Directory -Path $DGDTLWorkdir -Force | Out-Null
Copy-Item -Path "$DGDTLSoftware\examples\d01\data_*.csv", `
                "$DGDTLSoftware\examples\d01\DGDTL_Report_*.txt" `
          -Destination $DGDTLWorkdir
Set-Location $DGDTLWorkdir
```

Para otro dominio distribuido, siga su [README de ejemplo](../../examples/README.md).
Para sus propios datos, defina la misma variable de ruta del software y cambie
a su carpeta de trabajo preparada; coloque allí sus datos en vez de copiar
D01. Los resultados de referencia permanecen disponibles en la distribución
para una comparación opcional y no necesitan copiarse a una carpeta de nueva
ejecución.

## Unified: evaluación de configuración fija

Desde la carpeta de trabajo preparada, en Linux:

```bash
python "$DGDTL_SOFTWARE/orchestrators/dgdtl_unified_umaxp.py"
```

O en Windows:

```powershell
& "$DGDTLSoftware\orchestrators\Unified.cmd"
```

Seleccione **1 — Deployment Guide** o pulse Enter para aceptar el valor
predeterminado. Para D01, introduzca:

```text
DGDTL_Report_L1_Scout_4.txt
```

La guía proporciona la configuración del modelo y los parámetros de búsqueda.
En este modo, Unified lee `data_train.csv`, `data_valid.csv` y `data_test.csv`
desde la carpeta de trabajo actual y escribe en `results/`. El parser no toma
las rutas de entrada o salida de la guía. Una guía guardada en otra ubicación
no modifica dónde se resuelven las rutas predeterminadas de los CSV.

Para una configuración propia, seleccione **2 — Interactive Configuration**.
Introduzca el modo, el intercepto y la restricción de coeficientes, las rutas
de datos, la carpeta de salida y las fórmulas de características. El menú
posterior ofrece **Baseline Diagnosis (with Retraining Preview)**, **Run
Training (Auto/Custom Configuration)** y **Exit**. Siga las preguntas sobre
transformaciones y parámetros de entrenamiento de la acción seleccionada.
Unified no utiliza las opciones de línea de comandos de Hunter.

En Windows, las rutas dentro del diálogo Python de Unified corresponden a la
carpeta de trabajo montada en el contenedor. Utilice rutas relativas y barras
inclinadas hacia delante para las subcarpetas, no rutas de unidades de Windows.

## Hunter: búsqueda completa

Para el ejemplo D01 en Linux:

```bash
python "$DGDTL_SOFTWARE/orchestrators/dgdtl_hunter_umaxp_cluster.py" \
  --train data_train.csv --valid data_valid.csv --out-dir results_hunter \
  --mode raw --norm-y --formulas 'NBO_C1*sEpi'
```

La normalización y la fórmula de características de este comando corresponden
a D01. Utilice el README del dominio seleccionado para otros ejemplos y elija
las opciones de su propio estudio. La [tabla de opciones de Hunter](../../orchestrators/README.md#hunter-execute-the-full-search)
enumera los nueve argumentos y sus valores predeterminados. Escriba cada
fórmula entre comillas al pasarla por la shell. El ejemplo selecciona
explícitamente `results_hunter`; la carpeta de salida predeterminada del CLI
Python es `results_hunter_umaxp_cluster`.

En Windows:

```powershell
& "$DGDTLSoftware\orchestrators\Hunter.cmd"
```

El lanzador solicita la carpeta de datos y abre el diálogo de configuración.
Para D01, utilice el modo raw, active el intercepto y la normalización de
predictores y respuesta, deje desactivada la restricción de suma de coeficientes
e introduzca `NBO_C1*sEpi` como fórmula de características. Utilice
`data_train.csv`, `data_valid.csv` y `results_hunter` como rutas al seguir este
ejemplo. El transporte resuelve estas rutas respecto de la carpeta de trabajo
seleccionada en Windows; la carpeta de salida debe estar separada de los
archivos de entrada y fuera de la release.

Hunter requiere recursos de cómputo considerables. El paralelismo se define
internamente; su CLI no tiene opciones `--n-jobs` ni `--test`. Seleccione los
recursos y el tiempo de ejecución adecuados para su equipo. La
[descripción de los lanzadores](../../launchers/README.md) explica el generador
local opcional de Linux y la ayuda para clústeres institucionales. Ninguno
constituye una interfaz universal para planificadores de trabajos.

## Leer salidas y comparar referencias

La carpeta `results/` de Unified contiene salidas del modelo base, tablas de
soluciones de Run 1/Run 2, predicciones y métricas de los campeones y, con sus
módulos acompañantes, informes y figuras. Comience por
`DGDTL_Champion_Selection_Report.txt`. Hunter escribe guías de despliegue y
métricas; su evaluación final genera `UMaxP_Ranking_Framework.csv` y
`UMaxP_Framework_Report.txt` cuando dispone de registros. Lea los veredictos
antes de seleccionar una guía. La existencia de un informe no establece por
sí sola una certificación de despliegue exitosa.

Los cinco [ejemplos seleccionados](../../examples/README.md) son D01, D02, D08,
D11 y S03. Sus carpetas separadas `reference_results/unified/` y
`reference_results/hunter/` contienen 304 archivos de salidas Linux conservadas.
D11 conserva deliberadamente los diagnósticos `FAIL` de Hunter; la evaluación
de esa guía diagnóstica con Unified no la convierte en un campeón certificado
por Hunter. S03 pertenece a la colección de datos sintéticos de este estudio.
Cite las [publicaciones de los datos](../../examples/README.md#data-sources-and-references)
para los ejemplos empíricos y la [referencia del software](../../CITATION.cff).

Utilice las [reglas de procedencia y comparación](../../examples/REFERENCE_RESULTS.md)
al comparar las mismas entradas, configuración, entorno y flujo. Las
comparaciones científicas conservan valores numéricos exactos, orden,
clasificaciones, veredictos y selección de resultados. Aplique únicamente el
tratamiento documentado de fechas, duraciones y metadatos PDF; no introduzca
redondeos ni tolerancias numéricas para obtener concordancia. Conserve las
salidas originales al investigar diferencias.

El manifiesto de la release verifica los archivos distribuidos, no los nuevos
resultados. Las ejecuciones normales que escriben fuera de `software` no
requieren actualizar ningún manifiesto. Los hashes de referencia verifican las
copias conservadas; por sí solos no verifican una nueva ejecución científica.
Mantenga juntos los documentos y su manifiesto correspondiente al transferir
una distribución actualizada.

## Flujo recomendado

1. Para aprender la interfaz, comience con Unified y una guía de ejemplo;
   puede examinar las referencias conservadas sin repetir la búsqueda de Hunter.
2. Para un nuevo estudio, defina y conserve sus propias particiones de datos y
   decisiones de modelado. Utilice Hunter cuando necesite la búsqueda completa
   o el modo interactivo de Unified para una configuración propia.
3. Revise los informes estructurales y veredictos. Al continuar desde Hunter,
   seleccione la guía correspondiente y evalúela con Unified utilizando
   particiones de datos coherentes.
4. Conserve comandos u opciones interactivas, identidades del entorno y de los
   artefactos, hashes de entradas, guías, recursos utilizados y salidas
   originales junto con los resultados científicos.

En Linux también puede activar el entorno preparado y ejecutar sus propios
scripts Python utilizando `dgdtl_lts` y `u_maxp`. Consulte las
[API de DGDTL-LTS](../../packages/dgdtl-lts/README.md) y
[U-MaxP](../../packages/u-maxp/README.md). Los puntos de entrada de Windows
distribuidos cubren Hunter y Unified; no ofrecen un comando genérico para
ejecutar scripts propios.

## Límites de reproducibilidad

La reproducibilidad nativa en Linux se verificó en once dominios sobre dos
equipos independientes con Ubuntu 24.04 y dos clústeres de cómputo en Argentina,
bajo el entorno congelado. El [método de validación original](../../validation/VALIDATION_METHOD.md)
conserva ese alcance y su política de comparación exacta.

El runtime Linux certificado posteriormente reprodujo las salidas aprobadas
en Linux x86-64 con Docker y en Windows x86-64 mediante Docker Desktop/WSL2
con contenedores Linux para D01, D02, D08, D11 y S03, incluyendo Hunter,
Unified y su flujo combinado. Consulte la [procedencia del runtime](../../runtime/RUNTIME_PROVENANCE.json)
y la [procedencia de las referencias](../../examples/REFERENCE_RESULTS.md#execution-provenance-and-existing-certification).
Python nativo de Windows, macOS y las ejecuciones ARM quedan fuera de este
alcance certificado.

Las ejecuciones de ejemplos y las comprobaciones posteriores de experiencia
de usuario no constituyen una nueva certificación científica. Los ejemplos
enseñan el uso y permiten comparar resultados; no sustituyen el diseño de un
estudio independiente ni una validación externa. Esta actualización de los
manuales conserva intactos la implementación científica y los artefactos
certificados.
