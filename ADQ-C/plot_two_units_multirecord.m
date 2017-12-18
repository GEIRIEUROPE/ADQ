% Parse data  for multirecord-example with two units
% Simple example collects 4 records, this script plots these
nof_records = 4;
nof_units = 2;

for unit_nr = 1:nof_units
    for record_nr = 1:nof_records
        record_data{unit_nr}{record_nr} = load(['data' '_unit' num2str(unit_nr) '_record' num2str(record_nr-1) '.asc']);
    end
end


for unit_nr = 1:nof_units
    figure; clf;
    for record_nr = 1:nof_records
        data_size = size(record_data{unit_nr}{record_nr});
        nof_channels = data_size(2);
        for channel = 1:nof_channels
            subplot(nof_channels,1,channel);
            hold all;
            plot(record_data{unit_nr}{record_nr}(:,channel));
            ylabel('Code level');
            xlabel('Sample');
            title(['All records from channel ' num2str(channel) ' unit ' num2str(unit_nr)]) 
        end
    end
end