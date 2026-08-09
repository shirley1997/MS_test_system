# run in powershell
# $outDir = Join-Path (Get-Location) "effective-pom-checks"
$outDir = Join-Path (Get-Location) "ID-effective-pom-checks"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# options in test variable A and B1
$AValues  = "A1a","A1b","A2","A3"
$B1Values = "B1a","B1b","B1c","B1d"

# for each combination of A and B1, generate pom.xml
# then obtain effective-pom, then check if <repositories> block match the semantic meaning of the combination

$AValues  = "A1a","A1b","A2","A3"
$B1Values = "B1a","B1b","B1c","B1d"

foreach ($a in $AValues) {
  foreach ($b1 in $B1Values) {
    $tag = "$a-$b1"
    $pomFile   = Join-Path $outDir "pom-$tag.xml"
    $effFile   = Join-Path $outDir "effective-$tag.xml"
    $reposFile = Join-Path $outDir "repos-$tag.txt"

    python pom_override_check.py $a $b1 B2a "http://host.docker.internal:8081" $pomFile
    if ($LASTEXITCODE -ne 0) { continue }

    mvn help:effective-pom -f $pomFile "-Doutput=$effFile" -q

    $xml = Get-Content $effFile -Raw
    $repoBlock       = if ($xml -match '(?s)<repositories>.*?</repositories>') { $matches[0] } else { "(none)" }
    # $pluginRepoBlock = if ($xml -match '(?s)<pluginRepositories>.*?</pluginRepositories>') { $matches[0] } else { "(none)" }

    "===== $tag =====`n--- repositories ---`n$repoBlock" |
      Out-File -Encoding utf8 $reposFile
  }
}
