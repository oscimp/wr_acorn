graphics_toolkit('gnuplot')
d=dir('./File_001.CSV');
for l=1:length(d)
  d(l).name
  x=dlmread(d(l).name);
  for m=1:1
    hold on
    s=semilogx(x(170+15*m+4662*(m-1):170+15*m+4662*(m-1)+4662,1),x(170+15*m+4662*(m-1):170+15*m+4662*(m-1)+4662,2)-20*log10(62.5/10)+3);
    set(s, 'color', [.6, .6, .6]);
  end
end
d=dir('./phase_noise.csv');
for l=1:length(d)
  d(l).name
  x=dlmread(d(l).name);
  for m=1:4
    hold on
    s=semilogx(x(170+15*m+4662*(m-1):170+15*m+4662*(m-1)+4662,1),x(170+15*m+4662*(m-1):170+15*m+4662*(m-1)+4662,2)-20*log10(62.5/10)+3);
    set(s,'linestyle', ["--", "--", "-", "-"](m));
    set(s,'linewidth', [.5, .5, 3, 3](m));
    set(s,'color', ["r", "b", "r", "b"](m));
  end
end

%x=dlmread('welch_mmcm_sim');
%hold on
%semilogx(x(2:end, 1), 10*log10(x(2:end, 2)) + 20*log10(200/10));
%
%legend('MMCM phase shifting noise', 'MMCM phase shifting noise simulation')

legend('MMCM phase shifting noise', 'Recovered RX clk','SMA 100','WR ref=RXCLK','WR ref=SMA 100')
xlabel('frequency offset (Hz)')
ylabel('phase noise (dBrad²/Hz)')
xlim([1 1e6])
grid on
set (gcf, "papersize", [6.4, 4.8])
set (gcf, "paperposition", [0, 0, 6.4, 4.8])
print -dpdf phase_noise.pdf


