import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { writeFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const config = JSON.parse(process.env.LOGAI_AUTH_TEST_CONFIG);
let browser;
let phase = 'browser launch';
const checks = {};
const diagnostics=[];
try {
  browser = await chromium.launch({headless:true});
  for (const user of config.users) {
  const context = await browser.newContext();
  const page = await context.newPage();
  page.on('pageerror',error=>diagnostics.push(error.name));
  page.on('requestfailed',request=>{if(request.url().startsWith(config.api))diagnostics.push('business-request-failed');});
  let tokens;
  const authorizedRequests = [];
  page.on('response', async response => {
    if (response.url().split('?')[0] === config.keycloak + '/realms/gamestory-sso/protocol/openid-connect/token' && response.status() === 200) {
      tokens = await response.json();
    }
    if (response.url().startsWith(config.api + '/api/v1/') && response.status() === 200) {
      const request = response.request();
      if ((await request.allHeaders()).authorization?.startsWith('Bearer ')) authorizedRequests.push(response.url().split('?')[0]);
    }
  });
  phase = 'Keycloak local login form';
  await page.goto(config.ui + '/');
  await page.locator('#username').waitFor({timeout:45000});
  assert.equal(new URL(page.url()).searchParams.has('kc_idp_hint'), false);
  checks.noEntraRedirect = true;
  phase = 'local user password and required password update';
  await page.locator('#username').fill(user.username);
  await page.locator('#password').fill(config.rerun ? user.newPassword : user.password);
  await page.locator('#kc-login').click();
  if (!config.rerun) {
    await page.locator('#password-new').waitFor({timeout:30000});
    await page.locator('#password-new').fill(user.newPassword);
    await page.locator('#password-confirm').fill(user.newPassword);
    await page.locator('input[type=submit], button[type=submit]').first().click();
  }
  checks.firstLoginPasswordChange = true;
  checks.passwordPreservedAfterRerun = Boolean(config.rerun);
  phase = 'OIDC callback and authenticated UI';
  await page.getByRole('button',{name:'Logout',exact:true}).waitFor({timeout:45000});
  assert.equal(new URL(page.url()).origin, config.ui);
  assert.equal(new URL(page.url()).searchParams.has('code'), false);
  assert.equal(await page.evaluate(() => sessionStorage.getItem('logai-ui.access-token')), null);
  assert.equal(await page.evaluate(() => localStorage.getItem('logai-ui.access-token')), null);
  checks.callback = true;
  checks.tokensInMemoryOnly = true;
  for (let i=0;i<100 && !tokens?.access_token;i++) await page.waitForTimeout(100);
  assert.ok(tokens?.access_token);
  const claims = JSON.parse(Buffer.from(tokens.access_token.split('.')[1],'base64url').toString());
  assert.equal(claims.iss, config.keycloak + '/realms/gamestory-sso');
  assert.ok(claims.sub);
    assert.ok(claims.aud.includes('logai-api'));
  assert.ok(claims.realm_access.roles.includes(user.role));
  checks.tokenAudienceIssuerRoles = true;
  phase = 'identity and protected LogAI API requests';
  const headers = {Authorization:'Bearer '+tokens.access_token};
  assert.equal((await context.request.get(config.identity+'/me',{headers})).status(),200);
  const me = await (await context.request.get(config.identity+'/me',{headers})).json();
  assert.equal(me.sub,claims.sub);
  assert.ok(me.claims.realm_access.roles.includes(user.role));
  const release = await context.request.get(config.api+'/api/v1/release',{headers});
  assert.equal(release.status(),200);
  assert.equal((await release.json()).shipments.length,8);
  assert.equal((await context.request.get(config.api+'/api/v1/chutes',{headers})).status(),200);
  assert.equal((await context.request.get(config.api+'/api/v1/release')).status(),401);
  assert.equal((await context.request.get(config.api+'/api/v1/release',{headers:{Authorization:'Bearer invalid'}})).status(),401);
  assert.equal((await context.request.post(config.api+'/api/v1/callbacks/workflow-events',{headers,data:{event_type:'test',source:'test',tenant_id:'test',correlation_id:''}})).status(),403);
  assert.equal((await context.request.get(config.api+'/api/v1/admin/identity',{headers})).status(),user.role==='logai-admin'?200:403);
  checks.adminBoundary=true;
  checks.protectedEndpoints = true;
  checks.identityClaimsPreserved = true;
  checks.humanCannotCallTechnicalCallback = true;
  // Drive the actual application into the Schneider view to exercise its token-bearing fetch helper.
  phase = 'application API token propagation';
  const trigger = page.getByRole('button',{name:'Open Schneider Electric',exact:true});
  // Keyboard activation also covers the collapsed trigger whose label is off-screen.
  await trigger.focus();
  await trigger.press('Enter');
  await page.getByRole('link',{name:'Release',exact:true}).click();
  for(let i=0;i<100 && authorizedRequests.length===0;i++) await page.waitForTimeout(100);
  assert.ok(authorizedRequests.length>0,'Application did not send an authorized business API request');
  checks.applicationTokenPropagation = true;
  phase = 'logout and session termination';
  const refreshToken = tokens.refresh_token;
  await page.getByRole('button',{name:'Logout',exact:true}).click();
  await page.locator('#username').waitFor({timeout:45000});
  const refresh = await context.request.post(config.keycloak+'/realms/gamestory-sso/protocol/openid-connect/token',{
    form:{grant_type:'refresh_token',client_id:'logai-ui',refresh_token:refreshToken}
  });
  assert.equal(refresh.status(),400);
  checks.logout = true;
  checks.refreshSessionRevoked = true;
  checks[user.username] = {role:user.role,login:true,passwordChange:true,api:true,logout:true};
  await context.close();
  }
  phase = 'invalid password and disabled user';
  for (const credentials of [{username:'chris',password:config.users.find(u=>u.username==='chris').password},{username:config.disabledUsername,password:config.disabledPassword}]) {
    phase = credentials.username==='chris' ? 'invalid password rejection' : 'disabled user rejection';
    const deniedContext=await browser.newContext();
    const deniedPage=await deniedContext.newPage();
    await deniedPage.goto(config.ui+'/');
    await deniedPage.locator('#username').waitFor({timeout:45000});
    await deniedPage.locator('#username').fill(credentials.username);
    await deniedPage.locator('#password').fill(credentials.password);
    await deniedPage.locator('#kc-login').click();
    await deniedPage.getByText(/Invalid username or password|Account (?:is )?disabled/i).first().waitFor({timeout:15000});
    assert.equal(new URL(deniedPage.url()).origin,config.keycloak);
    await deniedContext.close();
  }
  checks.invalidPasswordAndDisabledUser=true;
  phase = 'fail-closed runtime configuration';
  const broken = await browser.newContext();
  const brokenPage = await broken.newPage();
  await brokenPage.route('**/config.json',route=>route.fulfill({status:503,contentType:'application/json',body:'{}'}));
  await brokenPage.goto(config.ui+'/');
  await brokenPage.getByText('Sign in required',{exact:true}).waitFor();
  assert.equal(await brokenPage.getByText('Local developer',{exact:true}).count(),0);
  checks.configFailureClosed = true;
  writeFileSync(config.rerun ? config.evidence.replace('.json','-rerun.json') : config.evidence, JSON.stringify({checks,engine:'Chromium',credentialsLogged:false},null,2)+'\n');
  console.log(JSON.stringify({checks}));
} catch (error) {
  console.error(JSON.stringify({phase,error:error.name,checks,diagnostics}));
  process.exitCode = 1;
} finally {
  if(browser) await browser.close();
}
