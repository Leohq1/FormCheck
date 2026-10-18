import { expect, test } from '@playwright/test'

test('guidance to upload to results happy path', async ({ page }) => {
  await page.goto('/')

  await expect(
    page.getByRole('heading', {
      name: /record one clip/i,
    }),
  ).toBeVisible()

  await page.getByRole('link', { name: /continue to upload/i }).click()
  await expect(
    page.getByRole('heading', { name: /upload your clip/i }),
  ).toBeVisible()

  await page.locator('input[type="file"]').setInputFiles({
    name: 'clear.mp4',
    mimeType: 'video/mp4',
    buffer: Buffer.from('mock-overhead-clear-bytes'),
  })
  await page.getByLabel(/dominant hand/i).selectOption('right')
  await page.getByLabel(/camera view/i).selectOption('side')
  await page.getByRole('checkbox').check()
  await page.getByRole('button', { name: /analyze clip/i }).click()

  await expect(page.getByText(/analyzing your clip/i)).toBeVisible()
  await expect(
    page.getByRole('heading', { name: /your coaching feedback/i }),
  ).toBeVisible({ timeout: 15_000 })
  await expect(page.getByText(/what to work on/i)).toBeVisible()
  await expect(page.getByText(/coaching suggestions/i)).toBeVisible()
  await expect(page.getByText(/reach through contact/i)).toBeVisible()
  await expect(page.getByText(/128 deg/i)).toBeVisible()
})
