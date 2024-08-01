const express = require("express");
const fs = require("fs");
const fsPromises = require("fs").promises;
const path = require("path");
const readline = require("readline");

const app = express();
const port = 3000;
const csvFolderPath = "./csv_files";

const selectedColumnIndex = 0;

const size = 1100;
const numnewlines = 11000
const speed=60
var startLine = 0;
var endLine = startLine + size;
var csvFiles
var randomFile;
async function Read(){
    const files = await fsPromises.readdir(csvFolderPath);
    csvFiles = files.filter((file) => path.extname(file).toLowerCase() === ".csv");
    randomFile = csvFiles[1];
}
app.get("/getECGData", async (req, res) => {
  try {
    if (csvFiles.length === 0) {
      return res.status(404).json({ error: "No CSV files found in the specified directory" });
    }

    
    startLine = startLine + speed;
    startLine %= numnewlines - size;
    endLine = startLine + size;
    console.log("Start line: " + startLine + " end " + endLine);

    const fileStream = fs.createReadStream(path.join(csvFolderPath, randomFile));
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity,
    });

    let lineCount = 0;
    let jsonData = [];

    for await (const line of rl) {
      lineCount++;
      if (lineCount >= startLine && lineCount <= endLine) {
        const values = line.split(",");
        const selectedValue = parseFloat(values[selectedColumnIndex]);
        jsonData.push(isNaN(selectedValue) ? null : selectedValue);
      }
      if (lineCount > endLine) break;
    }

    res.json(jsonData);
  } catch (error) {
    console.error("An error occurred:", error);
    res.status(500).json({ error: "An error occurred while processing the request" });
  }
});

app.listen(port,async () => {
  await Read();
  console.log(`Server is running on port ${port}`);
});
