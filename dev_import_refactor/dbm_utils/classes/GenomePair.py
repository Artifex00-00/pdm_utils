"""Represents a structure to pair two Genome objects and
perform comparisons between them to identify inconsistencies."""

from classes import Eval




class GenomePair:

    # Initialize all attributes:
    def __init__(self):

        # Initialize all non-calculated attributes:
        self.genome1 = None
        self.genome2 = None


        # Initialize calculated attributes
        self.evaluations = []

        self.matched_cds_list = [] # List of MatchedCds objects. TODO this contains perfect and imperfect matches
        self.unmatched_cds_genome1 = [] # List of CdsFeature objects
        self.unmatched_cds_genome2 = [] # List of CdsFeature objects



        self.perfect_matched_features_tally = 0
        self.imperfect_matched_features_tally = 0
        self.genome1_features_unmatched_tally = 0
        self.genome2_features_unmatched_tally = 0




    def copy_data(self, attr, first, second, keyword = None):
        """Copy data between paired genomes. The 'attr' parameter
        indicates the Genome object attribute used to identify direction
        of copy. The 'first' and 'second' parameters indicate the
        values of the attribute in each Genome to identiy
        which Genome will provide the data and which Genome
        will receive the data. The 'keyword' parameter is used as a filter
        to decide which Genome attribute data will be copied."""



        # Decide the direction of copy.
        direction = True
        if first == second:
            # If unable to identify direction of copy, set to False.
            direction = False
        elif attr == "type":
            if (self.genome1.type == first and self.genome2.type == second):
                first = self.genome1
                second = self.genome2
            elif (self.genome1.type == second and self.genome2.type == first):
                first = self.genome2
                second = self.genome1
            else:
                # If unable to identify direction of copy, set to False.
                direction = False
        elif attr == "id":
            if (self.genome1.id == first and \
                self.genome2.id == second):

                first = self.genome1
                second = self.genome2

            elif (self.genome1.id == second and \
                self.genome2.id == first):

                first = self.genome2
                second = self.genome1

            else:
                # If unable to identify direction of copy, set to False.
                direction = False
        else:
            direction = False


        # Now copy the data.
        if direction:

            # Do not copy over the 'type' attribute that is used to
            # differentiate the two genomes.
            if not attr == "id":
                if (second.id == keyword or keyword is None):
                    second.id = first.id
            if not attr == "type":
                if (second.type == keyword or keyword is None):
                    second.type = first.type

            # All other fields can be copied as needed.
            if (second.phage_name == keyword or keyword is None):
                second.phage_name = first.phage_name
            if (second.host_genus == keyword or keyword is None):
                second.host_genus = first.host_genus
            if (second.sequence == keyword or keyword is None):
                second.sequence = first.sequence
            if (second.accession == keyword or keyword is None):
                second.accession = first.accession
            if (second.author == keyword or keyword is None):
                second.author = first.author
            if (second.annotation_status == keyword or keyword is None):
                second.annotation_status = first.annotation_status
            if (second.cluster == keyword or keyword is None):
                second.cluster = first.cluster
            if (second.subcluster == keyword or keyword is None):
                second.subcluster = first.subcluster
            if (second.cluster_subcluster == keyword or keyword is None):
                second.cluster_subcluster = first.cluster_subcluster
            if (second.date_last_modified == keyword or keyword is None):
                second.date_last_modified = first.date_last_modified
            if (second.annotation_author == keyword or keyword is None):
                second.annotation_author = first.annotation_author
            if (second.annotation_qc == keyword or keyword is None):
                second.annotation_qc = first.annotation_qc
            if (second.retrieve_record == keyword or keyword is None):
                second.retrieve_record = first.retrieve_record
            if (second.record_name == keyword or keyword is None):
                second.record_name = first.record_name
            if (second.record_id == keyword or keyword is None):
                second.record_id = first.record_id
            if (second.record_accession == keyword or keyword is None):
                second.record_accession = first.record_accession
            if (second.record_description == keyword or keyword is None):
                second.record_description = first.record_description
            if (second.record_source == keyword or keyword is None):
                second.record_source = first.record_source
            if (second.record_organism == keyword or keyword is None):
                second.record_organism = first.record_organism
            if (second.record_authors == keyword or keyword is None):
                second.record_authors = first.record_authors
            if (second.record_date == keyword or keyword is None):
                second.record_date = first.record_date
            if (second.record_filename == keyword or keyword is None):
                second.record_filename = first.record_filename
            if (second.translation_table == keyword or keyword is None):
                second.translation_table = first.translation_table
            if (second.record == keyword or keyword is None):
                second.record = first.record
            if (second.search_name == keyword or keyword is None):
                second.search_name = first.search_name
            if (second._length == keyword or keyword is None):
                second._length = first._length
            if (second._gc == keyword or keyword is None):
                second._gc = first._gc
            if (second.evaluations == keyword or keyword is None):
                second.evaluations = first.evaluations
            if (second.cds_features == keyword or keyword is None):
                second.cds_features = first.cds_features
            if (second._cds_features_tally == keyword or keyword is None):
                second._cds_features_tally = first._cds_features_tally
            if (second._cds_start_end_ids == keyword or keyword is None):
                second._cds_start_end_ids = first._cds_start_end_ids
            if (second._cds_end_strand_ids == keyword or keyword is None):
                second._cds_end_strand_ids = first._cds_end_strand_ids
            if (second._cds_processed_primary_descriptions_tally == keyword \
                or keyword is None):

                second._cds_processed_primary_descriptions_tally = \
                    first._cds_processed_primary_descriptions_tally

            if (second.trna_features == keyword or keyword is None):
                second.trna_features = first.trna_features
            if (second._trna_features_tally == keyword or keyword is None):
                second._trna_features_tally = first._trna_features_tally
            if (second.source_features == keyword or keyword is None):
                second.source_features = first.source_features
            if (second._source_features_tally == keyword or keyword is None):
                second._source_features_tally = first._source_features_tally
            if (second.search_record_filename == keyword or keyword is None):
                second.search_record_filename = first.search_record_filename
            if (second._record_description_phage_name == keyword \
                or keyword is None):

                second._record_description_phage_name = \
                    first._record_description_phage_name

            if (second._record_source_phage_name == keyword \
                or keyword is None):

                second._record_source_phage_name = \
                    first._record_source_phage_name

            if (second._record_organism_phage_name == keyword \
                or keyword is None):

                second._record_organism_phage_name = \
                    first._record_organism_phage_name

            if (second._record_description_host_genus == keyword \
                or keyword is None):

                second._record_description_host_genus = \
                    first._record_description_host_genus

            if (second._record_source_host_genus == keyword or keyword is None):
                second._record_source_host_genus = \
                    first._record_source_host_genus
            if (second._record_organism_host_genus == keyword \
                or keyword is None):

                second._record_organism_host_genus = \
                    first._record_organism_host_genus

            if (second._cds_processed_product_descriptions_tally == keyword \
                or keyword is None):

                second._cds_processed_product_descriptions_tally = \
                    first._cds_processed_product_descriptions_tally

            if (second._cds_processed_function_descriptions_tally == keyword \
                or keyword is None):

                second._cds_processed_function_descriptions_tally = \
                    first._cds_processed_function_descriptions_tally

            if (second._cds_processed_note_descriptions_tally == keyword \
                or keyword is None):

                second._cds_processed_note_descriptions_tally = \
                    first._cds_processed_note_descriptions_tally

            if (second._cds_unique_start_end_ids == keyword \
                or keyword is None):

                second._cds_unique_start_end_ids = \
                    first._cds_unique_start_end_ids

            if (second._cds_duplicate_start_end_ids == keyword \
                or keyword is None):

                second._cds_duplicate_start_end_ids = \
                    first._cds_duplicate_start_end_ids

            if (second._cds_unique_end_strand_ids == keyword \
                or keyword is None):

                second._cds_unique_end_strand_ids = \
                    first._cds_unique_end_strand_ids

            if (second._cds_duplicate_end_strand_ids == keyword \
                or keyword is None):

                second._cds_duplicate_end_strand_ids = \
                    first._cds_duplicate_end_strand_ids




    # TODO finish revamping code for matching features.
    # TODO unit test.
    def match_cds_start_stop_ids(self):
        """Match annotated features in each genome with the same start and
        stop coordinates and the same strand (perfect match)."""


        # Create the perfect matched and unmatched sets.
        start_stop_ids_1 = self.genome1.get_cds_start_stop_ids()
        start_stop_ids_2 = self.genome2.get_cds_start_stop_ids()

        ids_matched, ids_1_unmatched, ids_2_unmatched = \
            FunctionsSimple.match_items(start_stop_ids_1, start_stop_ids_2)

        self.matched_cds_start_stop_ids.add(ids_matched)
        self.unmatched_cds_start_stop_ids_genome1 += ids_1_unmatched
        self.unmatched_cds_start_stop_ids_genome2 += ids_2_unmatched




    # TODO finish revamping code for matching features.
    # TODO unit test.
    def match_cds_stop_ids(self, list1, list2):
        """Match annotated features in each genome with the same stop
        coordinates and same strand but different start coordinates
        (imperfect match)."""

        # From the unmatched sets, created second round of
        # end-strand id sets.
        stop_ids_1 = []
        stop_ids_2 = []

        for start_stop_id in list1:
            stop_ids_1.append(start_stop_id[1])

        for start_stop_id in list2:
            stop_ids_2.append(start_stop_id[1])

        # Create the imperfect matched set
        ids_matched, ids_1_unmatched, ids_2_unmatched = \
            FunctionsSimple.match_items(start_stop_ids_1, start_stop_ids_2)


        self.matched_cds_stop_ids.add(ids_matched)
        self.unmatched_cds_stop_ids_genome1 += ids_1_unmatched
        self.unmatched_cds_stop_ids_genome2 += ids_2_unmatched






    # TODO finish revamping code for matching features.
    # TODO unit test.
    def match_cds_features(self):
        """Match annotated features in each genome with the same stop
        coordinates and same strand but different start coordinates
        (imperfect match)."""

        matched_start_stop_set = set(self.matched_cds_start_stop_ids)
        matched_stop_set = set(self.matched_cds_stop_ids)

        g1_feature_list = self.genome1.cds_features
        g2_feature_list = self.genome2.cds_features


        # Iterate through all cds features of each genome and assign
        # to the appropriate dictionary or list.
        g1_matched_cds_start_stop_dict = {}
        g1_matched_cds_stop_dict = {}
        g1_unmatched_cds_list = []


        for cds in g1_feature_list:
            if cds._start_stop_id in matched_start_stop_set:
                g1_matched_cds_start_stop_dict[cds._start_stop_id] = cds
            elif cds._stop_id in matched_stop_set:
                g1_matched_cds_stop_dict[cds._stop_id] = cds
            else:
                g1_unmatched_cds_list.append(cds)


        g2_matched_cds_start_stop_dict = {}
        g2_matched_cds_stop_dict = {}
        g2_unmatched_cds_list = []


        for cds in g2_feature_list:
            if cds._start_stop_id in matched_start_stop_set:
                g2_matched_cds_start_stop_dict[cds._start_stop_id] = cds
            elif cds._stop_id in matched_stop_set:
                g2_matched_cds_stop_dict[cds._stop_id] = cds
            else:
                g2_unmatched_cds_list.append(cds)


        # Create MatchedCdsFeatures objects
        for start_stop_tup in matched_start_stop_set:

            matched_cds_object = MatchedCdsFeatures()
            matched_cds_object.feature1 = \
                g1_matched_cds_start_stop_dict[start_stop_tup]
            matched_cds_object.feature2 = \
                g2_matched_cds_start_stop_dict[start_stop_tup]
            # TODO add a step to run all MatchedCDS evaluation methods?

            self.matched_start_stop_features.append(matched_cds_object)


        # Imperfectly matched features
        for end_strand_tup in imperfect_matched_cds_id_set:

            matched_cds_object = MatchedCdsFeatures()
            matched_cds_object.feature1 = \
                g1_matched_cds_stop_dict[end_strand_tup]
            matched_cds_object.feature2 = \
                ncbi_imperfect_matched_cds_dict[end_strand_tup]
            # TODO add a step to run all MatchedCDS evaluation methods?

            self.matched_stop_features.append(matched_cds_object)


        # Compute unmatched error and gene total errors for
        # all unmatched features.
        for cds in g1_unmatched_cds_list:
            cds.set_unmatched_error()
            cds.compute_total_cds_errors()
            if cds.get_total_errors() > 0:
                self.__total_number_genes_with_errors += 1

        for cds in ncbi_unmatched_cds_list:
            cds.set_unmatched_error()
            cds.compute_total_cds_errors()
            if cds.get_total_errors() > 0:
                self.__total_number_genes_with_errors += 1


        # Set unmatched cds lists
        self.genome1_unmatched_features = g1_unmatched_cds_list
        self.genome2_unmatched_features = g2_unmatched_cds_list


        # TODO not sure if I need this:
        # # Now compute the number of features in each category
        # self.__phamerator_ncbi_perfect_matched_features_tally = len(self.__phamerator_ncbi_perfect_matched_features)
        # self.__phamerator_ncbi_imperfect_matched_features_tally = len(self.__phamerator_ncbi_imperfect_matched_features)
        # self.__phamerator_features_unmatched_in_ncbi_tally = len(self.__phamerator_features_unmatched_in_ncbi)
        # self.__ncbi_features_unmatched_in_phamerator_tally = len(self.__ncbi_features_unmatched_in_phamerator)




        # TODO make sure this below is accounted for. If there is no
        # matching genome...
        # #If there is no matching NCBI genome, assign all Phamerator genes to Unmatched
        # else:
        #
        #     #Set unmatched cds lists, but do NOT count them in the unmatched tally.
        #     #The unmatched tally should reflect unmatched genes if there is actually a metching NCBI genome.
        #     self.__phamerator_features_unmatched_in_ncbi = g1_feature_list






















    # Evaluations



    def compare_id(self):
        """Compare the id of each genome."""

        if self.genome1.id != self.genome2.id:
            result = "The two genomes have different ids."
            status = "error"
        else:
            result = "The two genomes have the same ids."
            status = "correct"

        definition = "Compare the id of each genome."
        eval = Eval.Eval("TICKET", definition, result, status)
        self.evaluations.append(eval)



    def compare_genome_sequence(self):
        """Compare the sequence of each genome."""

        if self.genome1.sequence != self.genome2.sequence:
            result = "The two genomes have different sequences."
            status = "error"

        else:
            result = "The two sequences are the same."
            status = "correct"

        definition = "Compare the sequence of each genome."
        eval = Eval.Eval(id = "GENOMEPAIR0001", \
                        definition = definition, \
                        result = result, \
                        status = status)
        self.evaluations.append(eval)

    def compare_genome_length(self):
        """Compare the sequence length of each genome."""

        if self.genome1._length != self.genome2._length:
            result = "The two genomes have different sequence lengths."
            status = "error"
        else:
            result = "The two sequences are the same length."
            status = "correct"

        definition = "Compare the length of both sequences."
        eval = Eval.Eval(id = "GENOMEPAIR0002", \
                        definition = definition, \
                        result = result, \
                        status = status)
        self.evaluations.append(eval)


    def compare_cluster(self):
        """Compare the cluster of each genome."""

        if self.genome1.cluster != self.genome2.cluster:
            result = "The two genomes are assigned to different clusters."
            status = "error"
        else:
            result = "The two cluster designations are the same."
            status = "correct"

        definition = "Compare the cluster of both genomes."
        eval = Eval.Eval(id = "GENOMEPAIR0003", \
                        definition = definition, \
                        result = result, \
                        status = status)
        self.evaluations.append(eval)


    def compare_subcluster(self):
        """Compare the subcluster of each genome."""

        if self.genome1.subcluster != self.genome2.subcluster:
            result = "The two genomes are assigned to different subclusters."
            status = "error"
        else:
            result = "The two subcluster designations are the same."
            status = "correct"

        definition = "Compare the subcluster of both genomes."
        eval = Eval.Eval(id = "GENOMEPAIR0004", \
                        definition = definition, \
                        result = result, \
                        status = status)
        self.evaluations.append(eval)


    def compare_accession(self):
        """Compare the accession of each genome."""

        if self.genome1.accession != self.genome2.accession:
            result = "The two genomes have different accessions."
            status = "error"
        else:
            result = "The two accessions are the same."
            status = "correct"

        definition = "Compare the accession of both genomes."
        eval = Eval.Eval(id = "GENOMEPAIR0005", \
                        definition = definition, \
                        result = result, \
                        status = status)
        self.evaluations.append(eval)


    def compare_host_genus(self):
        """Compare the host_genus of each genome."""

        if self.genome1.host_genus != self.genome2.host_genus:
            result = "The two genomes have different hosts."
            status = "error"
        else:
            result = "The two hosts are the same."
            status = "correct"

        definition = "Compare the host_genus of both genomes."
        eval = Eval.Eval(id = "GENOMEPAIR0006", \
                        definition = definition, \
                        result = result, \
                        status = status)
        self.evaluations.append(eval)


    # TODO implement this method. Since authorship is not as straightforward
    # as other fields, it is tricky.
    def compare_author(self):
        """Compare the authorship of each genome."""
        pass
















###
