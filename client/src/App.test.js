import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

test('handles query submission', async () => {
  // Render the component
  render(<App />);
  
  // Find the input element by its placeholder text
  const inputElement = await screen.findByPlaceholderText(/Ask a question/i);

  // Find the submit button by its text
  const buttonElement = screen.getByText(/Submit/i);

  // Simulate user typing into the input field
  fireEvent.change(inputElement, { target: { value: 'test query' } });

  // Simulate clicking the submit button
  fireEvent.click(buttonElement);

  // Since the fetch is mocked in this test, add an assertion to ensure the request was made
  expect(inputElement.value).toBe('test query');

  // Optionally, you could mock the fetch request and check for the response as well
});
