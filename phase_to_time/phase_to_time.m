fc=1e7; % carrier frequency
N=1000;  % interpolation factor
% phase noise spectral SdBc @ fF
fF=  [1    10  100 1000 10000 1e5 1e6 1e7];
SdBc(:,1)=[-70  -70  -95  -120 -130 -130 -130 -130]; % BC/GM class I
SdBc(:,2)=[-100 -100 -115 -130 -140 -140 -140 -140]; % GM class II (LJ)
SdBc(:,3)=[-90  -90  -107 -125 -135 -135 -135 -135]  % BC class II

%%%%%%%% interpolate, convert SdBc to SdBrad & integrate over bandwidth bins
for count=1:3
  SdBcint=[];
  fFint=[];
  for k=1:length(SdBc(:,count))-1
     SdBcint=[SdBcint SdBc(k,count)+(SdBc(k+1,count)-SdBc(k,count))/(fF(k+1)-fF(k))*(linspace((fF(k)),(fF(k+1)),N)-fF(k))];
     fFint=[fFint logspace(log10(fF(k)),log10(fF(k+1)),N)];
  end

  SdBrad=SdBcint+3;   % dBc/Hz -> dBrad^2/Hz
  rad=sqrt(10.^(SdBrad(1:end-1)/10).*(fFint(2:end)-fFint(1:end-1))); % dBrad^2/Hz -> rad
  res=rad/2/pi/fc;    % rad -> s
  noweight=sqrt(sum(res.^2))   % integrate noise fluctuations
  % integrate noise fluctuations with weighing function: 1PPS sampled at tau0=+/-0.5 s
  % and H(f)=sin(2*pi*f*tau0) since PPS_{n+1}-PPS_n => H^2(f)=sin(2*pi*f*tau0).^2
  withweight=sqrt(sum((res.^2.*sin(2*pi*fFint(1:end-1)*1/2).^2)))
  subplot(211)
  semilogx(fFint,(SdBcint));
  hold on
  xlabel('Fourier frequency (Hz)')
  ylabel('Phase noise (dBc/Hz)')
end
