import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

// Mock fetch
beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  fetch.mockClear();
});

describe('App Component', () => {
  test('renders upload and query sections', () => {
    render(<App />);
  
    // Check if the upload section is rendered
    expect(screen.getByText(/Upload Document/i)).toBeInTheDocument();
  
    // Check if the query section heading is rendered
    expect(screen.getByRole('heading', { name: /Ask a Question/i })).toBeInTheDocument();
  });
  

  test('handles file upload successfully', async () => {
    // Mock the fetch response for file upload
    fetch.mockResolvedValueOnce({
      json: async () => ({ message: 'Document uploaded successfully' }),
    });
  
    render(<App />);
  
    // Simulate file selection
    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['dummy content'], 'testfile.txt', { type: 'text/plain' });
    fireEvent.change(fileInput, { target: { files: [file] } });
  
    // Simulate clicking the upload button (use getByRole to target the button)
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    fireEvent.click(uploadButton);
  
    // Check that the loading indicator appears
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBe(2); // Ensure both upload and query have progress bars
    expect(progressBars[0]).toBeInTheDocument();
  
  
    // Wait for the success message to appear
    await waitFor(() => {
      expect(screen.getByText(/Document uploaded successfully/i)).toBeInTheDocument();
    });
  
    // Ensure the loading indicator disappears after the upload is complete
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });
  

  test('handles file upload error', async () => {
    // Mock the fetch response for file upload error
    fetch.mockRejectedValueOnce(new Error('Upload failed'));
  
    render(<App />);
  
    // Simulate file selection
    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['dummy content'], 'testfile.txt', { type: 'text/plain' });
    fireEvent.change(fileInput, { target: { files: [file] } });
  
    // Simulate clicking the upload button (use getByRole for specificity)
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    fireEvent.click(uploadButton);
  
    // Check that the loading indicator appears
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBe(2); // Ensure both upload and query have progress bars
    expect(progressBars[0]).toBeInTheDocument();
  
    // Wait for the error message to appear
    await waitFor(() => {
      expect(screen.getByText(/Error uploading file/i)).toBeInTheDocument();
    });
  
    // Ensure the loading indicator disappears after the error
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });
  

  test('handles query submission successfully', async () => {
    // Mock the fetch response for query submission
    fetch.mockResolvedValueOnce({
      json: async () => ({ response: 'This is the query response.' }),
    });
  
    const { container } = render(<App />);
  
    // Simulate entering a query
    const queryInput = screen.getByLabelText(/ask a question/i);
    fireEvent.change(queryInput, { target: { value: 'What is React?' } });
  
    // Simulate clicking the submit button
    const submitButton = screen.getByText(/submit/i);
    fireEvent.click(submitButton);
  
    // Use container.querySelector to get the specific progress bar related to the query
    const queryProgressBar = container.querySelector('.MuiCircularProgress-root');
    expect(queryProgressBar).toBeInTheDocument();
  
    // Wait for the success response to appear
    await waitFor(() => {
      expect(screen.getByText(/This is the query response/i)).toBeInTheDocument();
    });
  
    // Ensure the loading indicator disappears after the query is complete
    await waitFor(() => {
      expect(queryProgressBar).not.toBeInTheDocument();
    });
  });
  

  test('handles query submission error', async () => {
    // Mock the fetch response for query submission error
    fetch.mockRejectedValueOnce(new Error('Query failed'));
  
    render(<App />);
  
    // Simulate entering a query
    const queryInput = screen.getByLabelText(/ask a question/i);
    fireEvent.change(queryInput, { target: { value: 'What is React?' } });
  
    // Simulate clicking the submit button
    const submitButton = screen.getByText(/submit/i);
    fireEvent.click(submitButton);
  
    // Check that the loading indicator appears (this is the second progressbar, likely the query section one)
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBe(2); // Ensure both upload and query have progress bars
    expect(progressBars[1]).toBeInTheDocument(); // This assumes the second progress bar is related to the query submission
  
    // Wait for the error response to appear
    await waitFor(() => {
      expect(screen.getByText(/Error fetching response/i)).toBeInTheDocument();
    });
  
    // Ensure the loading indicator disappears after the query is complete
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });  
});
