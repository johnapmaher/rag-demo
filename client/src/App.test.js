import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import App from './App';

test('renders RAG Demo title', () => {
  render(<App />);
  const titleElement = screen.getByText(/RAG Demo/i);
  expect(titleElement).toBeInTheDocument();
});

test('handles query submission', async () => {
  await act(async () => {
    render(<App />);
    screen.debug();
    const inputElement = await screen.getByPlaceholderText(/Ask a question/i);
    const buttonElement = screen.getByText(/Submit/i);

    fireEvent.change(inputElement, { target: { value: 'test query' } });
    fireEvent.click(buttonElement);
  });

  const responseElement = await screen.findByText(/Response:/i);
  expect(responseElement).toBeInTheDocument();
});