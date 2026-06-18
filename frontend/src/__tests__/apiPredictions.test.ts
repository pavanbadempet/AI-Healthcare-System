import {
  predictDiabetes,
  predictHeart,
  predictKidney,
  predictLiver,
  predictLungs,
  setTokenGetter,
} from '@/lib/api';

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  setTokenGetter(() => 'prediction-token');
});

function mockJsonResponse(body: unknown) {
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  });
}

describe('prediction API adapter', () => {
  it('posts screening payloads to versioned prediction endpoints', async () => {
    fetchMock.mockReturnValue(mockJsonResponse({
      prediction: 'Low Risk',
      confidence: 72,
      risk_level: 'Moderate',
    }));

    await predictDiabetes({ age: 51, bmi: 25 });
    await predictHeart({ age: 51, chol: 180 });
    await predictLiver({ age: 51, albumin: 3 });
    await predictKidney({ age: 51, bp: 120 });
    await predictLungs({ age: 51, smoking: 0 });

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      'http://127.0.0.1:8000/v1/predict/diabetes',
      'http://127.0.0.1:8000/v1/predict/heart',
      'http://127.0.0.1:8000/v1/predict/liver',
      'http://127.0.0.1:8000/v1/predict/kidney',
      'http://127.0.0.1:8000/v1/predict/lungs',
    ]);
    for (const [, options] of fetchMock.mock.calls) {
      expect(options).toMatchObject({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer prediction-token',
        },
      });
    }
  });
});
