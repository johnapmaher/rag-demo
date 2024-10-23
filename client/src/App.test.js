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

    // Check if the query section is rendered
    expect(screen.getByText(/Ask a Question/i)).toBeInTheDocument();
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

    // Simulate clicking the upload button
    const uploadButton = screen.getByText(/upload/i);
    fireEvent.click(uploadButton);

    // Check that the loading indicator appears
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Wait for the success message to appear
    await waitFor(() => {
      expect(screen.getByText(/Document uploaded successfully/i)).toBeInTheDocument();
    });

    // Ensure the loading indicator disappears after the upload is complete
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  test('handles file upload error', async () => {
    // Mock the fetch response for file upload error
    fetch.mockRejectedValueOnce(new Error('Upload failed'));

    render(<App />);

    // Simulate file selection
    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['dummy content'], 'testfile.txt', { type: 'text/plain' });
    fireEvent.change(fileInput, { target: { files: [file] } });

    // Simulate clicking the upload button
    const uploadButton = screen.getByText(/upload/i);
    fireEvent.click(uploadButton);

    // Check that the loading indicator appears
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Wait for the error message to appear
    await waitFor(() => {
      expect(screen.getByText(/Error uploading file/i)).toBeInTheDocument();
    });

    // Ensure the loading indicator disappears after the upload is complete
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  test('handles query submission successfully', async () => {
    // Mock the fetch response for query submission
    fetch.mockResolvedValueOnce({
      json: async () => ({ response: 'This is the query response.' }),
    });

    render(<App />);

    // Simulate entering a query
    const queryInput = screen.getByLabelText(/ask a question/i);
    fireEvent.change(queryInput, { target: { value: 'What is React?' } });

    // Simulate clicking the submit button
    const submitButton = screen.getByText(/submit/i);
    fireEvent.click(submitButton);

    // Check that the loading indicator appears
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Wait for the success response to appear
    await waitFor(() => {
      expect(screen.getByText(/This is the query response/i)).toBeInTheDocument();
    });

    // Ensure the loading indicator disappears after the query is complete
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
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

    // Check that the loading indicator appears
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Wait for the error response to appear
    await waitFor(() => {
      expect(screen.getByText(/Error fetching response/i)).toBeInTheDocument();
    });

    // Ensure the loading indicator disappears after the query is complete
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });
});
