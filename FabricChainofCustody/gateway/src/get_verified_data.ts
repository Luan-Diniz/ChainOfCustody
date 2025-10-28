import axios, { AxiosError } from 'axios';

// --- Configuration ---
const MOCK_DB_BASE_URL = 'http://localhost:49152';

interface PollOptions {
  /** The interval between retries in milliseconds. */
  intervalMs?: number;
  /** The maximum number of attempts before timing out. */
  maxAttempts?: number;
}

export async function pollForVerifiedData(
  identifier: string,
  options: PollOptions = {}
): Promise<any> {
  const { intervalMs = 2000, maxAttempts = 5 } = options; // Default: 2s interval, 10s total (5 * 2s)
  const url = `${MOCK_DB_BASE_URL}/verified-data/${identifier}`;

  console.log(`Polling for data with identifier "${identifier}"...`);

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      console.log(`[Attempt ${attempt}/${maxAttempts}] GET ${url}`);
      // Try to fetch the data
      const response = await axios.get(url);

      // Data found, parse it before deleting
      const data = JSON.parse(response.data);

      // Now, delete the data from the mock DB
      try {
        await axios.delete(url);
        console.log('...Data deleted successfully.');
      } catch (deleteError) {
        // Log the deletion error, but don't stop the process
        // The primary goal (getting the data) was successful.
        console.warn(`Could not delete data at ${url}:`, deleteError);
      }

      // Return the data we successfully retrieved
      return data;

    } catch (error) {
      const axiosError = error as AxiosError;
      // If we get a 404, it just means the data isn't ready yet.
      if (axiosError.response && axiosError.response.status === 404) {
        console.log('...Data not found yet.');
      } else {
        // For any other error (e.g., network issues), stop immediately.
        console.error('An unexpected error occurred:', error);
        throw new Error('Polling failed due to an unexpected error.');
      }
    }

    // Wait for the specified interval before the next attempt
    if (attempt < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
  }

  // If the loop finishes, we've timed out.
  throw new Error(`Polling timed out after ${maxAttempts} attempts.`);
}

/**
 * Example usage:

    await pollForVerifiedData(identifier, {
      intervalMs: 2000, // Check every 2 seconds
      maxAttempts: 15, // Try up to 15 times (30 seconds total)
    });
*/