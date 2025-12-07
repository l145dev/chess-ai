using System;
using System.IO;
using System.Text;

class Program
{
    // Config
    const string InputFile = "../lichess_db_raw.pgn"; // Input from data/lichess_db_raw.pgn
    const string OutputFile = "../elite_data/lichess_db.pgn"; // Output to data/elite_data/lichess_db.pgn
    const int MinElo = 2100;      // Filter for high tier players (tweak to get your ideal file size for training)
    const int MinTimeSec = 180;   // 180s = 3 mins (No Bullet)
    const bool CheckMoveCount = true; // Make sure move count is at least 20

    static void Main()
    {
        if (!File.Exists(InputFile))
        {
            Console.WriteLine($"Can't find {InputFile}");
            return;
        }

        Console.WriteLine($"Starting C# Filter...");
        Console.WriteLine($"Input: {InputFile}");
        Console.WriteLine($"Output: {OutputFile}");
        Console.WriteLine($"Criteria: AvgElo > {MinElo}, Time > {MinTimeSec}s");

        long gamesProcessed = 0;
        long gamesSaved = 0;

        // Using a large buffer for speed
        using (var fsIn = new FileStream(InputFile, FileMode.Open, FileAccess.Read, FileShare.Read, 65536))
        using (var reader = new StreamReader(fsIn, Encoding.ASCII))
        using (var fsOut = new FileStream(OutputFile, FileMode.Create, FileAccess.Write, FileShare.Read, 65536))
        using (var writer = new StreamWriter(fsOut, Encoding.ASCII))
        {
            string line;
            StringBuilder gameBuffer = new StringBuilder();

            // Stats holders
            int wElo = 0, bElo = 0;
            int baseTime = 0;
            bool headerFail = false;
            bool insideGame = false;

            while ((line = reader.ReadLine()) != null)
            {
                // New Game Detection (Lichess PGNs always start with [Event ...])
                if (line.StartsWith("[Event "))
                {
                    // Process the PREVIOUS game if we were inside one
                    if (insideGame && !headerFail && gameBuffer.Length > 0)
                    {
                        // Check move count (The Hack: look for " 20. " or "20.")
                        // We check the raw text in the buffer
                        string gameText = gameBuffer.ToString();
                        if (!CheckMoveCount || gameText.Contains(" 20. ") || gameText.Contains("20."))
                        {
                            writer.Write(gameText);
                            writer.WriteLine(); // Add spacing between games
                            gamesSaved++;
                        }
                    }

                    // Reset for NEW game
                    gamesProcessed++;
                    gameBuffer.Clear();
                    wElo = 0; bElo = 0; baseTime = 0;
                    headerFail = false;
                    insideGame = true;

                    if (gamesProcessed % 100000 == 0)
                        Console.Write($"\rProcessed: {gamesProcessed:N0} | Saved: {gamesSaved:N0}");
                }

                // If we already failed headers for this game, skip logic (just read until next Event)
                if (headerFail) continue;

                gameBuffer.AppendLine(line);

                // --- HEADER PARSING ---
                if (line.StartsWith("["))
                {
                    if (line.StartsWith("[WhiteElo "))
                        wElo = ParseIntAttribute(line);

                    else if (line.StartsWith("[BlackElo "))
                        bElo = ParseIntAttribute(line);

                    else if (line.StartsWith("[TimeControl "))
                    {
                        // Format is usually "300+0" or "600+5"
                        string val = ParseStringAttribute(line);
                        if (val.Contains("+"))
                        {
                            int.TryParse(val.Split('+')[0], out baseTime);
                        }
                    }
                }
                // End of headers usually indicated by empty line before moves
                else if (string.IsNullOrWhiteSpace(line))
                {
                    // Check Criteria immediately after headers are done
                    // Check Time
                    if (baseTime < MinTimeSec) { headerFail = true; continue; }

                    // Check Elo
                    if (wElo > 0 && bElo > 0)
                    {
                        if ((wElo + bElo) / 2 < MinElo) { headerFail = true; continue; }
                    }
                }
            }

            // Write the very last game if it was good
            if (insideGame && !headerFail && gameBuffer.Length > 0)
            {
                string gameText = gameBuffer.ToString();
                if (!CheckMoveCount || gameText.Contains(" 20. ") || gameText.Contains("20."))
                {
                    writer.Write(gameText);
                }
            }
        }

        Console.WriteLine($"\nDone! Saved {gamesSaved:N0} games out of {gamesProcessed:N0}.");
    }

    // fast helper to grab "2400" from [WhiteElo "2400"]
    static int ParseIntAttribute(string line)
    {
        int start = line.IndexOf('"');
        int end = line.LastIndexOf('"');
        if (start != -1 && end != -1 && end > start)
        {
            string sub = line.Substring(start + 1, end - start - 1);
            int.TryParse(sub, out int result);
            return result;
        }
        return 0;
    }

    static string ParseStringAttribute(string line)
    {
        int start = line.IndexOf('"');
        int end = line.LastIndexOf('"');
        if (start != -1 && end != -1 && end > start)
        {
            return line.Substring(start + 1, end - start - 1);
        }
        return "";
    }
}
