import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';

const NOTES_REPO = '/home/pcf/Desktop/projeler/RagProjects/KisiselNotArama';
const LLM_TIMEOUT = 150_000;

async function open(page: Page) {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Kod Repo Asistanı' })).toBeVisible();
}

async function ask(page: Page, q: string) {
  const box = page.getByLabel('Soru');
  await box.fill(q);
  await box.press('Enter');
}

async function pickMode(page: Page, mode: string) {
  await page.getByTestId('stSidebar').getByRole('combobox').first().click();
  await page.getByRole('option', { name: mode }).click();
  await expect(page.getByRole('combobox', { name: 'Arama modu' })).toHaveValue(mode);
}

test.describe('Sayfa', () => {
  test('yüklenir: başlık ve kontroller', async ({ page }) => {
    await open(page);
    await expect(page).toHaveTitle('Kod Repo Asistanı');
    await expect(page.getByLabel('Repo yolu')).toHaveValue(NOTES_REPO);
    await expect(page.getByLabel('Soru')).toBeVisible();
    await expect(page.getByRole('button', { name: 'İndeksle' })).toBeVisible();
    await expect(page.getByText('Arama modu')).toBeVisible();
    await expect(page.getByRole('combobox', { name: 'Arama modu' })).toHaveValue('hybrid');
  });

  test('mod seçimi değiştirilebilir', async ({ page }) => {
    await open(page);
    await pickMode(page, 'bm25');
  });
});

test.describe('Arama', () => {
  test('arama modu: kaynak blokları path:start-end başlığıyla görünür', async ({ page }) => {
    await open(page);
    await pickMode(page, 'bm25');
    await ask(page, 'indeks nasıl oluşturulur?');
    await expect(page.getByRole('heading', { name: 'Kaynaklar' })).toBeVisible({ timeout: LLM_TIMEOUT });
    const sources = page.getByTestId('stExpander');
    await expect(sources.first().getByText(/\S+:\d+-\d+/).first()).toBeVisible();
    expect(await sources.count()).toBeGreaterThan(0);
  });

  test('LLM cevabı üretilir ve hata göstermez', async ({ page }) => {
    await open(page);
    await ask(page, 'Bu repo ne işe yarar?');
    await expect(page.getByRole('heading', { name: 'Kaynaklar' })).toBeVisible({ timeout: LLM_TIMEOUT });
    await expect(page.getByText(/LLM hatası/)).toHaveCount(0);
    await expect(page.getByTestId('stSpinner')).toHaveCount(0);
    await expect(page.getByTestId('stMarkdownContainer').filter({ hasText: /\S{20,}/ }).first()).toBeVisible();
  });

  test('a11y: render sonrası DOM ve ekran görüntüsü kaydı', async ({ page }) => {
    await open(page);
    await ask(page, 'indeks');
    await expect(page.getByRole('heading', { name: 'Kaynaklar' })).toBeVisible({ timeout: LLM_TIMEOUT });
    const out = process.env.DOM_OUT;
    if (out) {
      fs.writeFileSync(out, await page.content());
      await page.screenshot({ path: out.replace(/\.html$/, '.png') });
    }
  });
});

test.describe('Geçersiz girdi', () => {
  test('boş repo yolu ile soru: çökmez', async ({ page }) => {
    await open(page);
    const repo = page.getByLabel('Repo yolu');
    await repo.fill('');
    await repo.press('Enter');
    await ask(page, 'merhaba');
    await expect(page.getByTestId('stException')).toHaveCount(0);
    await expect(page.getByText(/indeks yok|hata/i).first()).toBeVisible();
  });

  test('geçersiz repo yolu: uyarı gösterir', async ({ page }) => {
    await open(page);
    const repo = page.getByLabel('Repo yolu');
    await repo.fill('/yok/boyle/bir/yol');
    await repo.press('Enter');
    await ask(page, 'merhaba');
    await expect(page.getByText('Bu repo için indeks yok')).toBeVisible();
    await expect(page.getByTestId('stException')).toHaveCount(0);
  });

  test('geçersiz yol ile İndeksle: hata mesajı, çökme yok', async ({ page }) => {
    await open(page);
    const repo = page.getByLabel('Repo yolu');
    await repo.fill('/yok/boyle/bir/yol');
    await repo.press('Enter');
    await page.getByRole('button', { name: 'İndeksle' }).click();
    await expect(page.getByTestId('stSidebar').getByTestId('stAlert')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('stException')).toHaveCount(0);
  });
});
